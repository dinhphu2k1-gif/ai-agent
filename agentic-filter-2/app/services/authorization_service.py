from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.cache.invalidation import get_permission_version
from app.cache.keys import permission_snapshot_key
from app.cache.redis_client import UserContextCache
from app.repositories.policy_repo import LoadedPermission, PolicyRepository
from app.repositories.resource_repo import ResourceRepository
from app.services.permission_resolver import (
    ColumnMaskPolicy,
    DecisionType,
    PolicyDecision,
    collect_column_masks_from_bundle,
    resolve_from_bundle,
)
from app.services.user_context_service import UserContext

logger = logging.getLogger(__name__)

_SNAPSHOT_JSON_VERSION = 1


def _bundle_to_jsonable(bundle: list[LoadedPermission]) -> list[dict[str, Any]]:
    return [
        {
            "pid": str(b.permission_id),
            "rid": str(b.resource_id),
            "tn": b.permission_type_name,
            "ef": b.effect,
            "rf": list(b.row_filter_exprs),
            "mt": b.mask_type,
            "mp": b.mask_pattern,
        }
        for b in bundle
    ]


def _bundle_from_jsonable(rows: list[dict[str, Any]]) -> list[LoadedPermission]:
    out: list[LoadedPermission] = []
    for r in rows:
        out.append(
            LoadedPermission(
                permission_id=uuid.UUID(r["pid"]),
                resource_id=uuid.UUID(r["rid"]),
                permission_type_name=str(r["tn"]),
                effect=str(r["ef"]),
                row_filter_exprs=tuple(str(x) for x in r.get("rf", [])),
                mask_type=r.get("mt"),
                mask_pattern=r.get("mp"),
            )
        )
    return out


def _load_permission_bundle(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    ttl_seconds: int,
) -> list[LoadedPermission]:
    pv = get_permission_version()
    key = permission_snapshot_key(user_ctx.user_id)
    raw = cache.get(key)
    if raw:
        try:
            data = json.loads(raw.decode("utf-8"))
            if data.get("jv") == _SNAPSHOT_JSON_VERSION and int(data["pv"]) == pv:
                return _bundle_from_jsonable(data["bundle"])
        except (KeyError, TypeError, ValueError):
            pass
    return _load_fresh(session, user_ctx, cache, key, ttl_seconds, pv)


def resolve_access(
    session: Session,
    user_ctx: UserContext,
    target_resource_id: uuid.UUID,
    action: str,
    cache: UserContextCache,
    ttl_seconds: int,
) -> PolicyDecision:
    """
    Fail-closed PDP: on unexpected errors return DENY (Epic 5 / QA §15.3).
    Cache key permission_snapshot:{user_id} invalidated via permission_version (§10).
    """
    try:
        bundle = _load_permission_bundle(session, user_ctx, cache, ttl_seconds)
        rr = ResourceRepository(session)
        ancestors = rr.get_ancestor_resource_ids(target_resource_id)
        if not ancestors:
            return PolicyDecision(
                DecisionType.DENY,
                deny_reason="unknown_resource",
            )
        return resolve_from_bundle(
            bundle,
            frozenset(ancestors),
            action,
        )
    except Exception:
        logger.exception("policy resolve failed user_id=%s", user_ctx.user_id)
        return PolicyDecision(
            DecisionType.DENY,
            deny_reason="policy_resolve_error",
        )


def resolve_column_masks_for_resource(
    session: Session,
    user_ctx: UserContext,
    target_resource_id: uuid.UUID,
    cache: UserContextCache,
    ttl_seconds: int,
) -> tuple[ColumnMaskPolicy, ...]:
    """Mask policies for runtime SELECT (includes DESCRIBE grants with column_masks)."""
    try:
        bundle = _load_permission_bundle(session, user_ctx, cache, ttl_seconds)
        rr = ResourceRepository(session)
        ancestors = rr.get_ancestor_resource_ids(target_resource_id)
        if not ancestors:
            return ()
        return collect_column_masks_from_bundle(bundle, frozenset(ancestors))
    except Exception:
        logger.exception(
            "column mask resolve failed user_id=%s", user_ctx.user_id
        )
        return ()


def _load_fresh(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    key: str,
    ttl_seconds: int,
    pv: int,
) -> list[LoadedPermission]:
    repo = PolicyRepository(session)
    bundle = repo.load_permission_bundle(
        user_id=user_ctx.user_id,
        group_ids=user_ctx.group_ids,
        direct_role_ids=user_ctx.direct_role_ids,
        inherited_role_ids=user_ctx.inherited_role_ids,
    )
    payload = {
        "jv": _SNAPSHOT_JSON_VERSION,
        "pv": pv,
        "bundle": _bundle_to_jsonable(bundle),
    }
    cache.setex(key, ttl_seconds, json.dumps(payload).encode("utf-8"))
    return bundle
