from __future__ import annotations

import enum
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from app.repositories.policy_repo import LoadedPermission


# Runtime SELECT/masking also honors masks on DESCRIBE grants (common admin wizard setup).
DATA_ACCESS_MASK_ACTIONS: frozenset[str] = frozenset({"SELECT", "DESCRIBE"})


class DecisionType(str, enum.Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ALLOW_WITH_FILTER = "ALLOW_WITH_FILTER"
    ALLOW_WITH_MASK = "ALLOW_WITH_MASK"
    ALLOW_WITH_FILTER_AND_MASK = "ALLOW_WITH_FILTER_AND_MASK"


@dataclass(frozen=True)
class ColumnMaskPolicy:
    permission_id: uuid.UUID
    mask_type: str
    mask_pattern: str | None


@dataclass(frozen=True)
class PolicyDecision:
    decision: DecisionType
    row_filter_exprs: tuple[str, ...] = ()
    column_masks: tuple[ColumnMaskPolicy, ...] = ()
    deny_reason: str | None = None


def resolve_from_bundle(
    bundle: Sequence[LoadedPermission],
    ancestor_ids: frozenset[uuid.UUID],
    action: str,
) -> PolicyDecision:
    """PDP core: §7.1 matching, §7.2 DENY precedence, default deny, row filter aggregation."""
    action_u = action.strip().upper()
    candidates = [
        b
        for b in bundle
        if b.permission_type_name.upper() == action_u and b.resource_id in ancestor_ids
    ]
    if any(b.effect.upper() == "DENY" for b in candidates):
        return PolicyDecision(DecisionType.DENY, deny_reason="explicit_deny")

    allows = [b for b in candidates if b.effect.upper() == "ALLOW"]
    if not allows:
        return PolicyDecision(DecisionType.DENY, deny_reason="default_deny")

    row_exprs: list[str] = []
    seen: set[str] = set()
    for b in allows:
        for expr in b.row_filter_exprs:
            if expr not in seen:
                seen.add(expr)
                row_exprs.append(expr)

    masks: list[ColumnMaskPolicy] = []
    seen_m: set[tuple[uuid.UUID, str, str | None]] = set()
    for b in allows:
        if b.mask_type:
            key = (b.permission_id, b.mask_type, b.mask_pattern)
            if key not in seen_m:
                seen_m.add(key)
                masks.append(
                    ColumnMaskPolicy(
                        permission_id=b.permission_id,
                        mask_type=b.mask_type,
                        mask_pattern=b.mask_pattern,
                    )
                )

    has_rf = bool(row_exprs)
    has_mk = bool(masks)
    if has_rf and has_mk:
        dt = DecisionType.ALLOW_WITH_FILTER_AND_MASK
    elif has_rf:
        dt = DecisionType.ALLOW_WITH_FILTER
    elif has_mk:
        dt = DecisionType.ALLOW_WITH_MASK
    else:
        dt = DecisionType.ALLOW

    return PolicyDecision(
        decision=dt,
        row_filter_exprs=tuple(row_exprs),
        column_masks=tuple(masks),
    )


def collect_column_masks_from_bundle(
    bundle: Sequence[LoadedPermission],
    ancestor_ids: frozenset[uuid.UUID],
    mask_actions: frozenset[str] = DATA_ACCESS_MASK_ACTIONS,
) -> tuple[ColumnMaskPolicy, ...]:
    """
    Column masks for runtime data access (/sql/execute, /filter/search).

    SELECT authorization is evaluated separately; masks are often stored on DESCRIBE
    permissions when configured via the admin column-mask wizard.
    """
    actions_u = {a.strip().upper() for a in mask_actions}
    masks: list[ColumnMaskPolicy] = []
    seen: set[tuple[uuid.UUID, str, str | None]] = set()
    for b in bundle:
        if b.permission_type_name.upper() not in actions_u:
            continue
        if b.resource_id not in ancestor_ids:
            continue
        if b.effect.upper() != "ALLOW":
            continue
        if not b.mask_type:
            continue
        key = (b.permission_id, b.mask_type, b.mask_pattern)
        if key in seen:
            continue
        seen.add(key)
        masks.append(
            ColumnMaskPolicy(
                permission_id=b.permission_id,
                mask_type=b.mask_type,
                mask_pattern=b.mask_pattern,
            )
        )
    return tuple(masks)
