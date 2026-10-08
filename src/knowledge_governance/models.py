"""S1 identity, organization and project tables.

Database constraints make an ops project use the reserved key "ops".
Together with unique(organization_id, project_key), this permits at most
one ops project per organization. The service creates it in the same
transaction as its organization.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .ids import new_id


class Base(DeclarativeBase):
    pass


class Principal(Base):
    __tablename__ = "principals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    external_subject: Mapped[str | None] = mapped_column(String(191), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('user','builtin_agent','service_agent','connector')", name="ck_principal_type"),
        CheckConstraint("status IN ('active','disabled')", name="ck_principal_status"),
    )


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active','suspended','archived')", name="ck_organization_status"),
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    project_key: Mapped[str] = mapped_column(String(64), nullable=False)
    project_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    system_managed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("principals.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "project_key", name="uq_project_org_key"),
        UniqueConstraint("id", "organization_id", name="uq_project_id_org"),
        CheckConstraint(
            "(project_kind = 'ops' AND project_key = 'ops' AND system_managed = 1 AND status = 'active') "
            "OR (project_kind = 'business' AND project_key <> 'ops' AND system_managed = 0)",
            name="ck_project_kind_key",
        ),
        CheckConstraint("status IN ('active','suspended','archived')", name="ck_project_status"),
    )


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    principal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "principal_id", name="uq_membership_org_principal"),
        CheckConstraint("role IN ('org_owner','org_admin','org_billing_admin','org_auditor','org_member')", name="ck_membership_role"),
        CheckConstraint("status IN ('active','revoked')", name="ck_membership_status"),
    )


class RoleBinding(Base):
    __tablename__ = "role_bindings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    principal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(["project_id", "organization_id"], ["projects.id", "projects.organization_id"], ondelete="RESTRICT", name="fk_role_binding_project_org"),
        UniqueConstraint("project_id", "principal_id", "role", name="uq_project_role_principal"),
        CheckConstraint(
            "role IN ('project_owner','project_contributor','business_approver','publisher','project_viewer','ops_operator')",
            name="ck_project_role",
        ),
        CheckConstraint("status IN ('active','revoked')", name="ck_project_role_status"),
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    principal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    request_path: Mapped[str] = mapped_column(String(191), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("principal_id", "request_path", "idempotency_key", name="uq_idempotency_request"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(String(36))
    actor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "organization_id"],
            ["projects.id", "projects.organization_id"],
            ondelete="RESTRICT",
        ),
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(String(36))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivery_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "organization_id"],
            ["projects.id", "projects.organization_id"],
            ondelete="RESTRICT",
        ),
    )
