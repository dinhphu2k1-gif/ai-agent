#!/usr/bin/env python3
"""Seed one integration user (agri-agent) with group, role, and COREDB permissions.

Tạo user cố định, group ``agri_integration``, role ``Agri_Integration_Reader`` với
SELECT + DESCRIBE (+ USAGE) ALLOW trên database ``COREDB`` (kế thừa xuống schema/table/column).

Chạy sau khi catalog COREDB đã có (``seed_gl_resource_dictionary.py``):

  python scripts/seed_agri_integration_user.py

Biến môi trường:
  AGRI_INTEGRATION_USERNAME   — mặc định ``agri_agent`` (truyền vào metadata API ``userId``)
  AGRI_INTEGRATION_USER_ID    — UUID user (tùy chọn; mặc định uuid5 ổn định)
  AGRI_INTEGRATION_EMAIL      — mặc định agri_agent@local.dev
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.seed_gl_resource_dictionary import DATABASE_NAME  # noqa: E402

AGRI_INTEGRATION_NS = uuid.UUID("b2b2b2b2-b2b2-4b2b-8b2b-b2b2b2b2b2b2")

DEFAULT_USERNAME = "agri_agent"
DEFAULT_EMAIL = "agri_agent@local.dev"
DEFAULT_ROLE_NAME = "Agri_Integration_Reader"
DEFAULT_GROUP_NAME = "agri_integration"

PERMISSION_ACTIONS = ("USAGE", "SELECT", "DESCRIBE")


def agri_stable_id(label: str) -> uuid.UUID:
    return uuid.uuid5(AGRI_INTEGRATION_NS, label)


def integration_user_id() -> uuid.UUID:
    raw = os.environ.get("AGRI_INTEGRATION_USER_ID", "").strip()
    if raw:
        return uuid.UUID(raw)
    return agri_stable_id("user-agri-agent")


def integration_username() -> str:
    return os.environ.get("AGRI_INTEGRATION_USERNAME", DEFAULT_USERNAME).strip() or DEFAULT_USERNAME


def integration_email() -> str:
    return os.environ.get("AGRI_INTEGRATION_EMAIL", DEFAULT_EMAIL).strip() or DEFAULT_EMAIL


def _ensure_permission_types(session: Session) -> None:
    from app.models.permission import PermissionType

    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            session.add(PermissionType(name=name))
    session.flush()


def _ptype_id(session: Session, name: str) -> uuid.UUID:
    from app.models.permission import PermissionType

    return session.scalars(
        select(PermissionType.id).where(PermissionType.name == name)
    ).one()


def _ensure_role_permission(
    session: Session,
    *,
    role_id: uuid.UUID,
    perm_id: uuid.UUID,
    resource_id: uuid.UUID,
    permission_type_id: uuid.UUID,
    effect: str,
) -> None:
    from app.models.permission import Permission
    from app.repositories.identity_repo import IdentityRepository

    ir = IdentityRepository(session)
    perm = session.get(Permission, perm_id)
    if perm is None:
        session.add(
            Permission(
                id=perm_id,
                resource_id=resource_id,
                permission_type_id=permission_type_id,
                effect=effect,
            )
        )
    else:
        perm.resource_id = resource_id
        perm.permission_type_id = permission_type_id
        perm.effect = effect
    session.flush()
    ir.add_role_permission(role_id, perm_id)


def seed_agri_integration_user(session: Session) -> dict[str, object]:
    """
    Idempotent: user + group + role + membership + ALLOW USAGE/SELECT/DESCRIBE on COREDB.
    """
    from app.models.identity import Group, Role, User
    from app.repositories.identity_repo import IdentityRepository
    from app.repositories.resource_repo import ResourceRepository

    user_id = integration_user_id()
    username = integration_username()
    email = integration_email()
    role_id = agri_stable_id("role-agri-integration")
    group_id = agri_stable_id("group-agri-integration")

    ir = IdentityRepository(session)
    rr = ResourceRepository(session)

    db_rid = rr.find_database_resource_id_by_name(DATABASE_NAME)
    if db_rid is None:
        raise RuntimeError(
            f"Database resource '{DATABASE_NAME}' not found. "
            "Run: python scripts/seed_gl_resource_dictionary.py"
        )

    user = session.get(User, user_id)
    if user is None:
        session.add(
            User(
                id=user_id,
                username=username,
                email=email,
                full_name="Agri Metadata Integration",
                is_active=True,
            )
        )
    else:
        user.username = username
        user.email = email
        user.full_name = "Agri Metadata Integration"
        user.is_active = True
    session.flush()

    role = session.get(Role, role_id)
    if role is None:
        session.add(
            Role(
                id=role_id,
                name=DEFAULT_ROLE_NAME,
                display_name="Agri agent — metadata & SQL integration",
            )
        )
    else:
        role.name = DEFAULT_ROLE_NAME
        role.display_name = "Agri agent — metadata & SQL integration"
    session.flush()

    group = session.get(Group, group_id)
    if group is None:
        session.add(
            Group(
                id=group_id,
                name=DEFAULT_GROUP_NAME,
                description="Integration tests with agentic-agri metadata_agent",
            )
        )
    else:
        group.name = DEFAULT_GROUP_NAME
        group.description = "Integration tests with agentic-agri metadata_agent"
    session.flush()

    ir.add_user_to_group(user_id, group_id)
    ir.add_group_role(group_id, role_id)
    ir.add_user_role(user_id, role_id)

    permissions_created: list[str] = []
    for action in PERMISSION_ACTIONS:
        perm_id = agri_stable_id(f"perm-agri-coredb-{action.lower()}")
        _ensure_role_permission(
            session,
            role_id=role_id,
            perm_id=perm_id,
            resource_id=db_rid,
            permission_type_id=_ptype_id(session, action),
            effect="ALLOW",
        )
        permissions_created.append(action)

    session.flush()
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "role_id": role_id,
        "role_name": DEFAULT_ROLE_NAME,
        "group_id": group_id,
        "group_name": DEFAULT_GROUP_NAME,
        "database_name": DATABASE_NAME,
        "database_resource_id": db_rid,
        "permissions": permissions_created,
    }


def main() -> None:
    from app.core.config import Settings

    settings = Settings()
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        try:
            _ensure_permission_types(session)
            info = seed_agri_integration_user(session)
            session.commit()
        except OperationalError as exc:
            print(
                "\n[seed_agri_integration_user] PostgreSQL connection failed.\n"
                "  Start Postgres and set DATABASE_URL in .env.\n"
                f"  URL: {settings.database_url}\n",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()

    print("--- Agri integration user seed OK ---")
    print(f"userId (metadata API): {info['username']}")
    print(f"user_id: {info['user_id']}")
    print(f"group: {info['group_name']} ({info['group_id']})")
    print(f"role: {info['role_name']} ({info['role_id']})")
    print(f"database: {info['database_name']} resource={info['database_resource_id']}")
    print(f"role permissions ALLOW: {', '.join(info['permissions'])}")
    print(
        "Test metadata: POST /api/v1/metadata/keyword-search "
        f'{{"userId": "{info["username"]}", "query": "journal", "size": 10}}'
    )


if __name__ == "__main__":
    main()
