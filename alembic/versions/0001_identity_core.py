"""identity_core

Revision ID: 0001
Revises:
Create Date: 2026-10-08 10:58:35.141423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('organizations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.Column('timezone', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("status IN ('active','suspended','archived')", name='ck_organization_status'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('principals',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('external_subject', sa.String(length=191), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("status IN ('active','disabled')", name='ck_principal_status'),
    sa.CheckConstraint("type IN ('user','builtin_agent','service_agent','connector')", name='ck_principal_type'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('external_subject')
    )
    op.create_table('idempotency_records',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('principal_id', sa.String(length=36), nullable=False),
    sa.Column('request_path', sa.String(length=191), nullable=False),
    sa.Column('idempotency_key', sa.String(length=36), nullable=False),
    sa.Column('request_hash', sa.String(length=64), nullable=False),
    sa.Column('resource_id', sa.String(length=36), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['principal_id'], ['principals.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('principal_id', 'request_path', 'idempotency_key', name='uq_idempotency_request')
    )
    op.create_table('organization_memberships',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('principal_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("role IN ('org_owner','org_admin','org_billing_admin','org_auditor','org_member')", name='ck_membership_role'),
    sa.CheckConstraint("status IN ('active','revoked')", name='ck_membership_status'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['principal_id'], ['principals.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', 'principal_id', name='uq_membership_org_principal')
    )
    op.create_table('projects',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('project_key', sa.String(length=64), nullable=False),
    sa.Column('project_kind', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('purpose', sa.String(length=255), nullable=False),
    sa.Column('timezone', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('system_managed', sa.Boolean(), nullable=False),
    sa.Column('owner_id', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("(project_kind = 'ops' AND project_key = 'ops' AND system_managed = 1 AND status = 'active') OR (project_kind = 'business' AND project_key <> 'ops' AND system_managed = 0)", name='ck_project_kind_key'),
    sa.CheckConstraint("status IN ('active','suspended','archived')", name='ck_project_status'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['owner_id'], ['principals.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'organization_id', name='uq_project_id_org'),
    sa.UniqueConstraint('organization_id', 'project_key', name='uq_project_org_key')
    )
    op.create_index(op.f('ix_projects_organization_id'), 'projects', ['organization_id'], unique=False)
    op.create_table('audit_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=True),
    sa.Column('actor_id', sa.String(length=36), nullable=False),
    sa.Column('action', sa.String(length=64), nullable=False),
    sa.Column('resource_type', sa.String(length=32), nullable=False),
    sa.Column('resource_id', sa.String(length=36), nullable=False),
    sa.Column('request_hash', sa.String(length=64), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['principals.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['project_id', 'organization_id'], ['projects.id', 'projects.organization_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('outbox_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=True),
    sa.Column('event_type', sa.String(length=64), nullable=False),
    sa.Column('aggregate_id', sa.String(length=36), nullable=False),
    sa.Column('payload', sa.Text(), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('delivery_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['project_id', 'organization_id'], ['projects.id', 'projects.organization_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('role_bindings',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('principal_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("role IN ('project_owner','project_contributor','business_approver','publisher','project_viewer','ops_operator')", name='ck_project_role'),
    sa.CheckConstraint("status IN ('active','revoked')", name='ck_project_role_status'),
    sa.ForeignKeyConstraint(['principal_id'], ['principals.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['project_id', 'organization_id'], ['projects.id', 'projects.organization_id'], name='fk_role_binding_project_org', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'principal_id', 'role', name='uq_project_role_principal')
    )

    _create_guard_triggers()


def downgrade() -> None:
    _drop_guard_triggers()
    op.drop_table('role_bindings')
    op.drop_table('outbox_events')
    op.drop_table('audit_events')
    op.drop_index(op.f('ix_projects_organization_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_table('organization_memberships')
    op.drop_table('idempotency_records')
    op.drop_table('principals')
    op.drop_table('organizations')


_GUARDS = ("guard_ops_delete", "guard_ops_identity", "guard_audit_update", "guard_audit_delete")


def _create_guard_triggers() -> None:
    dialect = op.get_context().dialect.name
    if dialect == "sqlite":
        op.execute("""CREATE TRIGGER guard_ops_delete BEFORE DELETE ON projects
            WHEN OLD.project_kind = 'ops'
            BEGIN SELECT RAISE(ABORT, 'system_ops_immutable'); END""")
        op.execute("""CREATE TRIGGER guard_ops_identity BEFORE UPDATE ON projects
            WHEN OLD.project_kind = 'ops' AND (
                NEW.organization_id <> OLD.organization_id OR NEW.project_kind <> OLD.project_kind
                OR NEW.project_key <> OLD.project_key OR NEW.system_managed <> OLD.system_managed)
            BEGIN SELECT RAISE(ABORT, 'system_ops_immutable'); END""")
        for action in ("update", "delete"):
            op.execute(f"""CREATE TRIGGER guard_audit_{action} BEFORE {action.upper()} ON audit_events
                BEGIN SELECT RAISE(ABORT, 'audit_append_only'); END""")
    elif dialect == "mysql":
        op.execute("""CREATE TRIGGER guard_ops_delete BEFORE DELETE ON projects FOR EACH ROW
            BEGIN IF OLD.project_kind = 'ops' THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'system_ops_immutable';
            END IF; END""")
        op.execute("""CREATE TRIGGER guard_ops_identity BEFORE UPDATE ON projects FOR EACH ROW
            BEGIN IF OLD.project_kind = 'ops' AND (
                NEW.organization_id <> OLD.organization_id OR NEW.project_kind <> OLD.project_kind
                OR NEW.project_key <> OLD.project_key OR NEW.system_managed <> OLD.system_managed)
            THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'system_ops_immutable';
            END IF; END""")
        for action in ("update", "delete"):
            op.execute(f"""CREATE TRIGGER guard_audit_{action} BEFORE {action.upper()} ON audit_events
                FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_append_only'""")
    else:
        raise RuntimeError("S1 migration currently supports MySQL 8.0.16+ and SQLite only")


def _drop_guard_triggers() -> None:
    for name in _GUARDS:
        op.execute(f"DROP TRIGGER IF EXISTS {name}")
