from datetime import datetime, timedelta, timezone
from io import StringIO
import os
import unittest
from unittest.mock import patch
import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from knowledge_governance.db import make_engine
from knowledge_governance.identity import (
    Conflict, Forbidden, create_business_project, create_organization, effective_access,
)
from knowledge_governance.models import (
    AuditEvent, IdempotencyRecord, Organization, OrganizationMembership, OutboxEvent,
    Principal, Project, RoleBinding,
)


class IdentityCoreTests(unittest.TestCase):
    def setUp(self):
        self.engine = make_engine("sqlite:///:memory:")

        with self.engine.begin() as connection:
            cfg = Config("alembic.ini")
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with Session(self.engine, expire_on_commit=False) as session:
            self.owner = Principal(type="user")
            self.other = Principal(type="user")
            self.agent = Principal(type="service_agent")
            session.add_all([self.owner, self.other, self.agent])
            session.commit()

    def tearDown(self):
        self.engine.dispose()

    def make_org(self, slug="acme", key=None):
        with Session(self.engine, expire_on_commit=False) as session:
            return create_organization(
                session, actor_id=self.owner.id, idempotency_key=key or str(uuid.uuid4()),
                name="Acme", slug=slug, timezone="Asia/Shanghai",
            )

    def make_project(self, org, key="sales"):
        with Session(self.engine, expire_on_commit=False) as session:
            return create_business_project(
                session, actor_id=self.owner.id, organization_id=org.id,
                idempotency_key=str(uuid.uuid4()), project_key=key,
                name="Sales", purpose="approved sales knowledge",
            )

    def access(self, principal, org, project):
        with Session(self.engine) as session:
            return effective_access(
                session, principal_id=principal.id,
                organization_id=org.id, project_id=project.id,
            )

    def test_creation_is_atomic_and_idempotent(self):
        key = str(uuid.uuid4())
        org, ops = self.make_org(key=key)
        org2, ops2 = self.make_org(key=key)
        self.assertEqual((org.id, ops.id), (org2.id, ops2.id))
        self.assertEqual(uuid.UUID(org.id).version, 7)
        with Session(self.engine) as session:
            for model in (Organization, Project, OrganizationMembership, AuditEvent, OutboxEvent, IdempotencyRecord):
                self.assertEqual(session.scalar(select(func.count()).select_from(model)), 1)
        self.assertEqual(ops.project_kind, "ops")
        self.assertTrue(ops.system_managed)

    def test_same_key_with_different_body_conflicts(self):
        key = str(uuid.uuid4())
        self.make_org(key=key)
        with self.assertRaisesRegex(Conflict, "idempotency_conflict"):
            self.make_org(slug="another", key=key)

    def test_ops_failure_rolls_back_organization_and_events(self):
        with Session(self.engine) as session:
            @event.listens_for(session, "before_flush")
            def fail_ops(current, *_):
                if any(isinstance(obj, Project) for obj in current.new):
                    raise RuntimeError("simulated ops insert failure")

            with self.assertRaisesRegex(RuntimeError, "simulated"):
                create_organization(
                    session, actor_id=self.owner.id, idempotency_key=str(uuid.uuid4()),
                    name="Acme", slug="atomic", timezone="UTC",
                )
        with Session(self.engine) as session:
            for model in (Organization, Project, OrganizationMembership, AuditEvent, OutboxEvent, IdempotencyRecord):
                self.assertEqual(session.scalar(select(func.count()).select_from(model)), 0)

    def test_ops_cannot_be_deleted_retyped_or_relocated(self):
        org, ops = self.make_org()
        other_org, _ = self.make_org("other")
        statements = [
            ("DELETE FROM projects WHERE id=:id", {}),
            ("UPDATE projects SET project_key='converted', project_kind='business', system_managed=0 WHERE id=:id", {}),
            ("UPDATE projects SET organization_id=:org WHERE id=:id", {"org": other_org.id}),
        ]
        for sql, extra in statements:
            with self.subTest(sql=sql), self.assertRaisesRegex(IntegrityError, "system_ops_immutable"):
                with self.engine.begin() as connection:
                    connection.execute(text(sql), {"id": ops.id, **extra})

    def test_database_rejects_second_ops_and_reserved_key(self):
        org, ops = self.make_org()
        for key, kind, managed in (("ops", "ops", True), ("ops-two", "ops", True), ("ops", "business", False)):
            with self.subTest(key=key, kind=kind), self.assertRaises(IntegrityError):
                with Session(self.engine) as session, session.begin():
                    session.add(Project(
                        organization_id=org.id, project_key=key, project_kind=kind,
                        name="invalid", purpose="invalid", timezone="UTC", system_managed=managed,
                    ))

    def test_audit_is_append_only(self):
        self.make_org()
        for sql in ("UPDATE audit_events SET action='changed'", "DELETE FROM audit_events"):
            with self.subTest(sql=sql), self.assertRaisesRegex(IntegrityError, "audit_append_only"):
                with self.engine.begin() as connection:
                    connection.execute(text(sql))

    def test_org_admin_has_ops_metadata_but_no_business_access(self):
        org, ops = self.make_org()
        project = self.make_project(org)
        with Session(self.engine) as session, session.begin():
            session.add(OrganizationMembership(
                organization_id=org.id, principal_id=self.other.id, role="org_admin",
            ))
        self.assertEqual(self.access(self.other, org, ops).capabilities, ("ops:read_metadata",))
        self.assertFalse(self.access(self.other, org, project).allowed)
        self.assertTrue(self.access(self.owner, org, project).allowed)

    def test_cross_org_and_unbound_agent_denied(self):
        org, ops = self.make_org()
        project = self.make_project(org)
        other_org, _ = self.make_org("other")
        self.assertFalse(self.access(self.owner, other_org, project).allowed)
        self.assertFalse(self.access(self.agent, org, ops).allowed)
        with Session(self.engine) as session, self.assertRaises(Forbidden):
            create_organization(
                session, actor_id=self.agent.id, idempotency_key=str(uuid.uuid4()),
                name="Agent", slug="agent-org", timezone="UTC",
            )

    def test_revocation_and_expiry_remove_access(self):
        org, _ = self.make_org()
        project = self.make_project(org)
        with Session(self.engine) as session, session.begin():
            session.add(OrganizationMembership(
                organization_id=org.id, principal_id=self.other.id, role="org_member",
            ))
            session.add(RoleBinding(
                organization_id=org.id, project_id=project.id,
                principal_id=self.other.id, role="project_viewer",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            ))
        self.assertFalse(self.access(self.other, org, project).allowed)
        with Session(self.engine, expire_on_commit=False) as reader:
            # Keep the principal in this session's identity map to test refresh.
            cached = reader.get(Principal, self.owner.id)
            self.assertEqual(cached.status, "active")
            reader.commit()
            with Session(self.engine) as writer, writer.begin():
                writer.execute(update(Principal).where(Principal.id == self.owner.id).values(status="disabled"))
            result = effective_access(reader, principal_id=self.owner.id, organization_id=org.id, project_id=project.id)
            self.assertFalse(result.allowed)

    def test_membership_revocation_blocks_access_and_idempotency_replay(self):
        key = str(uuid.uuid4())
        org, ops = self.make_org(key=key)
        with Session(self.engine) as session, session.begin():
            session.execute(update(OrganizationMembership).where(
                OrganizationMembership.organization_id == org.id,
            ).values(status="revoked"))
        self.assertFalse(self.access(self.owner, org, ops).allowed)
        with self.assertRaises(Forbidden):
            self.make_org(key=key)

    def test_role_binding_cannot_claim_another_organization(self):
        org, _ = self.make_org()
        other_org, _ = self.make_org("other")
        project = self.make_project(org)
        with self.assertRaises(IntegrityError):
            with Session(self.engine) as session, session.begin():
                session.add(RoleBinding(
                    organization_id=other_org.id, project_id=project.id,
                    principal_id=self.other.id, role="project_viewer",
                ))

    def test_migration_can_downgrade_empty_database(self):
        with self.engine.begin() as connection:
            # Remove the setup principals; no organization data exists in this case.
            connection.execute(text("DELETE FROM principals"))
            cfg = Config("alembic.ini")
            cfg.attributes["connection"] = connection
            command.downgrade(cfg, "base")
            command.upgrade(cfg, "head")


    def test_migration_matches_current_models(self):
        with self.engine.begin() as connection:
            cfg = Config("alembic.ini")
            cfg.attributes["connection"] = connection
            command.check(cfg)

    def test_suspended_org_blocks_cached_idempotency_replay(self):
        key = str(uuid.uuid4())
        org, _ = self.make_org(key=key)
        with Session(self.engine, expire_on_commit=False) as reader:
            cached = reader.get(Organization, org.id)
            reader.commit()
            with Session(self.engine) as writer, writer.begin():
                writer.execute(update(Organization).where(Organization.id == org.id).values(status="suspended"))
            self.assertEqual(cached.status, "active")
            with self.assertRaises(Forbidden):
                create_organization(
                    reader, actor_id=self.owner.id, idempotency_key=key,
                    name="Acme", slug="acme", timezone="Asia/Shanghai",
                )

    def test_demoted_admin_cannot_create_project_from_cached_role(self):
        org, _ = self.make_org()
        with Session(self.engine, expire_on_commit=False) as reader:
            cached = reader.scalar(select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org.id,
                OrganizationMembership.principal_id == self.owner.id,
            ))
            reader.commit()
            with Session(self.engine) as writer, writer.begin():
                writer.execute(update(OrganizationMembership).where(
                    OrganizationMembership.id == cached.id,
                ).values(role="org_member"))
            self.assertEqual(cached.role, "org_owner")
            with self.assertRaises(Forbidden):
                create_business_project(
                    reader, actor_id=self.owner.id, organization_id=org.id,
                    idempotency_key=str(uuid.uuid4()), project_key="new",
                    name="New", purpose="Test",
                )

    def test_expired_idempotency_key_can_be_reused(self):
        key = str(uuid.uuid4())
        org, _ = self.make_org(key=key)
        with Session(self.engine) as session, session.begin():
            session.execute(update(IdempotencyRecord).values(
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            ))
        new_org, _ = self.make_org(slug="new-org", key=key)
        self.assertNotEqual(org.id, new_org.id)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(IdempotencyRecord)), 1)
            self.assertEqual(session.scalar(select(func.count()).select_from(AuditEvent)), 2)

    def test_mysql_migration_renders_guards_without_connecting(self):
        output = StringIO()
        cfg = Config("alembic.ini", output_buffer=output)
        with patch.dict(os.environ, {"DATABASE_URL": "mysql+pymysql://unused:unused@localhost/unused"}):
            command.upgrade(cfg, "head", sql=True)
        sql = output.getvalue()
        self.assertIn("CREATE TABLE projects", sql)
        self.assertIn("CREATE TRIGGER guard_ops_delete", sql)
        self.assertIn("SIGNAL SQLSTATE '45000'", sql)


if __name__ == "__main__":
    unittest.main()
