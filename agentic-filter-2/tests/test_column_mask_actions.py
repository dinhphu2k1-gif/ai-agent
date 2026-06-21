"""Column masks on DESCRIBE grants apply to runtime SELECT paths."""

from __future__ import annotations

import uuid

from app.repositories.policy_repo import LoadedPermission
from app.services.permission_resolver import collect_column_masks_from_bundle


def test_collect_mask_from_describe_permission_on_column() -> None:
    col_rid = uuid.uuid4()
    bundle = [
        LoadedPermission(
            permission_id=uuid.uuid4(),
            resource_id=col_rid,
            permission_type_name="DESCRIBE",
            effect="ALLOW",
            row_filter_exprs=(),
            mask_type="PARTIAL",
            mask_pattern="XXX",
        ),
        LoadedPermission(
            permission_id=uuid.uuid4(),
            resource_id=col_rid,
            permission_type_name="SELECT",
            effect="ALLOW",
            row_filter_exprs=(),
            mask_type=None,
            mask_pattern=None,
        ),
    ]
    masks = collect_column_masks_from_bundle(bundle, frozenset({col_rid}))
    assert len(masks) == 1
    assert masks[0].mask_type == "PARTIAL"
    assert masks[0].mask_pattern == "XXX"
