"""Transactional S1 organization/project operations and initial human access policy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as utc_timezone
from functools import wraps
import hashlib
import json
import re
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import (
    AuditEvent, IdempotencyRecord, Organization, OrganizationMembership,
    OutboxEvent, Principal, Project, RoleBinding,
)

_KEY = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_BUSINESS_ROLES = {
    "project_owner": ("projects:read", "project:manage", "sources:read", "knowledge:read"),
    "project_contributor": ("projects:read", "sources:read", "knowledge:read"),
    "business_approver": ("projects:read", "sources:read", "issues:read"),
    "publisher": ("projects:read", "knowledge:read"),
    "project_viewer": ("projects:read", "knowledge:read"),
}


class DomainError(Exception):
    pass


class Conflict(DomainError):
    pass


class Forbidden(DomainError):
    pass


class NotFound(DomainError):
    pass


@dataclass(frozen=True)
class AccessDecision:
    capabilities: tuple[str, ...]
    reason_code: str

    @property
    def allowed(self) -> bool:
        return bool(self.capabilities)


def _request_hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_idempotency_key(key: str) -> str:
    try:
        parsed = uuid.UUID(key)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("idempotency_key must be a UUID") from exc
    return str(parsed)


def _existing_result(session: Session, principal_id: str, path: str, key: str, digest: str) -> str | None:
    record = session.scalar(select(IdempotencyRecord).where(
        IdempotencyRecord.principal_id == principal_id,
        IdempotencyRecord.request_path == path,
        IdempotencyRecord.idempotency_key == key,
    ))
    if record is None:
        return None
    expiry = record.expires_at.replace(tzinfo=utc_timezone.utc)
    if expiry <= datetime.now(utc_timezone.utc):
        session.delete(record)
        session.flush()
        return None
    if record.request_hash != digest:
        raise Conflict("idempotency_conflict")
    return record.resource_id


def _require_active_user(session: Session, principal_id: str) -> None:
    principal = session.scalar(select(Principal).where(Principal.id == principal_id).execution_options(populate_existing=True))
    if principal is None or principal.type != "user" or principal.status != "active":
        raise Forbidden("active_user_required")


def _record_write(
    session: Session, *, principal_id: str, path: str, key: str, digest: str,
    organization_id: str, project_id: str | None, resource_type: str,
    resource_id: str, action: str,
) -> None:
    session.add(IdempotencyRecord(
        principal_id=principal_id, request_path=path, idempotency_key=key,
        request_hash=digest, resource_id=resource_id,
        expires_at=datetime.now(utc_timezone.utc) + timedelta(hours=24),
    ))
    session.add(AuditEvent(
        organization_id=organization_id, project_id=project_id, actor_id=principal_id,
        action=action, resource_type=resource_type, resource_id=resource_id,
        request_hash=digest,
    ))
    session.add(OutboxEvent(
        organization_id=organization_id, project_id=project_id,
        event_type=action, aggregate_id=resource_id,
        payload=json.dumps({"resource_type": resource_type, "resource_id": resource_id}),
    ))


def _retry_unique_race(operation):
    @wraps(operation)
    def wrapped(session, **kwargs):
        for attempt in range(2):
            try:
                return operation(session, **kwargs)
            except IntegrityError as exc:
                if attempt:
                    raise Conflict("constraint_conflict") from exc
        raise AssertionError("unreachable")
    return wrapped


@_retry_unique_race
def create_organization(
    session: Session, *, actor_id: str, idempotency_key: str,
    name: str, slug: str, timezone: str,
) -> tuple[Organization, Project]:
    """Create organization, its sole ops project, owner membership and events atomically."""
    if not name.strip() or len(name) > 128 or len(timezone) > 64 or not _KEY.fullmatch(slug):
        raise ValueError("invalid organization fields")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("invalid timezone") from exc
    key = _validate_idempotency_key(idempotency_key)
    path = "/api/v1/organizations"
    digest = _request_hash({"name": name, "slug": slug, "timezone": timezone})
    with session.begin():
        _require_active_user(session, actor_id)
        prior_id = _existing_result(session, actor_id, path, key, digest)
        if prior_id is not None:
            organization = session.get(Organization, prior_id, populate_existing=True)
            ops = session.scalar(select(Project).where(
                Project.organization_id == prior_id, Project.project_key == "ops"
            ))
            if organization is None or ops is None:
                raise Conflict("idempotency_record_inconsistent")
            member = session.scalar(select(OrganizationMembership).where(
                OrganizationMembership.organization_id == prior_id,
                OrganizationMembership.principal_id == actor_id,
                OrganizationMembership.status == "active",
            ).execution_options(populate_existing=True))
            if member is None or organization.status != "active":
                raise Forbidden("organization_access_revoked")
            return organization, ops
        if session.scalar(select(Organization.id).where(Organization.slug == slug)):
            raise Conflict("organization_slug_taken")
        organization = Organization(name=name, slug=slug, timezone=timezone)
        session.add(organization)
        session.flush()
        ops = Project(
            organization_id=organization.id, project_key="ops", project_kind="ops",
            name="系统运营", purpose="组织运营配置与健康摘要",
            timezone=timezone, status="active", system_managed=True,
        )
        session.add(ops)
        session.flush()
        session.add(OrganizationMembership(
            organization_id=organization.id, principal_id=actor_id, role="org_owner",
        ))
        _record_write(
            session, principal_id=actor_id, path=path, key=key, digest=digest,
            organization_id=organization.id, project_id=ops.id,
            resource_type="organization", resource_id=organization.id,
            action="organization_created",
        )
    return organization, ops


@_retry_unique_race
def create_business_project(
    session: Session, *, actor_id: str, organization_id: str, idempotency_key: str,
    project_key: str, name: str, purpose: str,
) -> Project:
    if project_key == "ops" or not _KEY.fullmatch(project_key):
        raise ValueError("invalid business project key")
    if not name.strip() or len(name) > 128 or not purpose.strip() or len(purpose) > 255:
        raise ValueError("name and purpose required")
    key = _validate_idempotency_key(idempotency_key)
    path = f"/api/v1/organizations/{organization_id}/projects"
    digest = _request_hash({"project_key": project_key, "name": name, "purpose": purpose})
    with session.begin():
        _require_active_user(session, actor_id)
        org = session.get(Organization, organization_id, populate_existing=True)
        member = session.scalar(select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.principal_id == actor_id,
            OrganizationMembership.status == "active",
        ).execution_options(populate_existing=True))
        if org is None or org.status != "active" or member is None or member.role not in {"org_owner", "org_admin"}:
            raise Forbidden("projects_write_required")
        prior_id = _existing_result(session, actor_id, path, key, digest)
        if prior_id is not None:
            project = session.get(Project, prior_id, populate_existing=True)
            if project is None:
                raise Conflict("idempotency_record_inconsistent")
            return project
        if session.scalar(select(Project.id).where(
            Project.organization_id == organization_id, Project.project_key == project_key
        )):
            raise Conflict("project_key_taken")
        project = Project(
            organization_id=organization_id, project_key=project_key,
            project_kind="business", name=name, purpose=purpose,
            timezone=org.timezone, status="active", system_managed=False, owner_id=actor_id,
        )
        session.add(project)
        session.flush()
        session.add(RoleBinding(
            organization_id=organization_id, project_id=project.id, principal_id=actor_id, role="project_owner",
        ))
        _record_write(
            session, principal_id=actor_id, path=path, key=key, digest=digest,
            organization_id=organization_id, project_id=project.id,
            resource_type="project", resource_id=project.id, action="project_created",
        )
    return project


def effective_access(
    session: Session, *, principal_id: str, organization_id: str, project_id: str,
) -> AccessDecision:
    """Return currently effective human capabilities; agents fail closed until bound."""
    principal = session.scalar(select(Principal).where(Principal.id == principal_id).execution_options(populate_existing=True))
    org = session.scalar(select(Organization).where(Organization.id == organization_id).execution_options(populate_existing=True))
    project = session.scalar(select(Project).where(Project.id == project_id).execution_options(populate_existing=True))
    if (
        principal is None or principal.type != "user" or principal.status != "active"
        or org is None or org.status != "active"
        or project is None or project.organization_id != organization_id or project.status != "active"
    ):
        return AccessDecision((), "not_found_or_forbidden")
    membership = session.scalar(select(OrganizationMembership).where(
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.principal_id == principal_id,
        OrganizationMembership.status == "active",
    ).execution_options(populate_existing=True))
    if membership is None:
        return AccessDecision((), "not_found_or_forbidden")
    bindings = session.scalars(select(RoleBinding).where(
        RoleBinding.organization_id == organization_id,
        RoleBinding.project_id == project_id,
        RoleBinding.principal_id == principal_id,
        RoleBinding.status == "active",
    ).execution_options(populate_existing=True)).all()
    now = datetime.now(utc_timezone.utc)
    bindings = [b for b in bindings if b.expires_at is None or b.expires_at.replace(tzinfo=utc_timezone.utc) > now]
    if project.project_kind == "ops":
        if membership.role in {"org_owner", "org_admin"} or any(b.role == "ops_operator" for b in bindings):
            return AccessDecision(("ops:read_metadata",), "allowed")
        return AccessDecision((), "not_found_or_forbidden")
    capabilities: set[str] = set()
    for binding in bindings:
        capabilities.update(_BUSINESS_ROLES.get(binding.role, ()))
    if capabilities:
        return AccessDecision(tuple(sorted(capabilities)), "allowed")
    return AccessDecision((), "not_found_or_forbidden")
