"""Column masking on /sql/execute must use executor result keys (often lowercase)."""

from __future__ import annotations

import uuid

from app.services.masking_service import (
    apply_column_masks_to_rows,
    logical_column_to_result_keys,
)
from app.services.permission_resolver import ColumnMaskPolicy


def test_logical_column_mapping_case_insensitive_result_keys() -> None:
    mapping = logical_column_to_result_keys(
        ("FULL_NAME", "ADDRESS_LINE"),
        ["address_line", "full_name"],
    )
    assert mapping["FULL_NAME"] == "full_name"
    assert mapping["ADDRESS_LINE"] == "address_line"


def test_mask_both_columns_with_qualified_table_keys() -> None:
    pol = ColumnMaskPolicy(
        permission_id=uuid.uuid4(), mask_type="FULL", mask_pattern=None
    )
    rows = [{"full_name": "Nguyen Van A", "address_line": "123 Street"}]
    keys = ["full_name", "address_line"]
    logical = ("FULL_NAME", "ADDRESS_LINE")
    masks = {
        ("CIF_CUSTOMERS", "FULL_NAME"): pol,
        ("CIF_ADDRESSES", "ADDRESS_LINE"): pol,
        "FULL_NAME": pol,
        "ADDRESS_LINE": pol,
    }

    apply_column_masks_to_rows(
        rows,
        keys,
        logical,
        masks,
        hash_salt="dev-masking-salt-change-in-prod",
        projections=(
            ("FULL_NAME", "CIF_CUSTOMERS", "FULL_NAME"),
            ("ADDRESS_LINE", "CIF_ADDRESSES", "ADDRESS_LINE"),
        ),
    )

    assert rows[0]["full_name"] == "*" * len("Nguyen Van A")
    assert rows[0]["address_line"] == "*" * len("123 Street")


def test_mask_both_full_name_and_address_line() -> None:
    pol = ColumnMaskPolicy(
        permission_id=uuid.uuid4(), mask_type="FULL", mask_pattern=None
    )
    rows = [{"full_name": "Nguyen Van A", "address_line": "123 Street"}]
    keys = ["full_name", "address_line"]
    logical = ("FULL_NAME", "ADDRESS_LINE")
    masks = {"FULL_NAME": pol, "ADDRESS_LINE": pol}

    apply_column_masks_to_rows(
        rows, keys, logical, masks, hash_salt="dev-masking-salt-change-in-prod"
    )

    assert rows[0]["full_name"] == "*" * len("Nguyen Van A")
    assert rows[0]["address_line"] == "*" * len("123 Street")


def test_mask_full_name_when_postgres_returns_lowercase_key() -> None:
    pol = ColumnMaskPolicy(
        permission_id=uuid.uuid4(), mask_type="FULL", mask_pattern=None
    )
    rows = [{"full_name": "Nguyen Van A", "address_line": "123 Street"}]
    keys = ["full_name", "address_line"]
    logical = ("FULL_NAME", "ADDRESS_LINE")
    masks = {"FULL_NAME": pol}

    apply_column_masks_to_rows(
        rows, keys, logical, masks, hash_salt="dev-masking-salt-change-in-prod"
    )

    assert rows[0]["full_name"] == "*" * len("Nguyen Van A")
    assert rows[0]["address_line"] == "123 Street"
