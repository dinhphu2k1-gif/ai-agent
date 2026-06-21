"""jsonable_cell must accept all common PostgreSQL driver scalars."""

from __future__ import annotations

import enum
import ipaddress
import json
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest

from app.services.masking_service import jsonable_cell, jsonable_row


class _Color(enum.Enum):
    RED = "red"


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        (True, True),
        (42, 42),
        ("text", "text"),
        (3.14, 3.14),
        (Decimal("99.99"), 99.99),
        (uuid.UUID("550e8400-e29b-41d4-a716-446655440000"), "550e8400-e29b-41d4-a716-446655440000"),
        (date(2024, 6, 1), "2024-06-01"),
        (datetime(2024, 6, 1, 15, 30, 0), "2024-06-01T15:30:00"),
        (time(9, 0, 5), "09:00:05"),
        (timedelta(hours=2, minutes=30), 9000.0),
        (_Color.RED, "red"),
        (ipaddress.IPv4Address("10.0.0.1"), "10.0.0.1"),
        (b"bytes", "bytes"),
        ({"nested": Decimal("1.5")}, {"nested": 1.5}),
        ([date(2024, 1, 1), date(2024, 1, 2)], ["2024-01-01", "2024-01-02"]),
    ],
)
def test_jsonable_cell_types(value: object, expected: object) -> None:
    out = jsonable_cell(value)
    assert out == expected
    json.dumps(out)


def test_jsonable_cell_nan_and_inf_become_null() -> None:
    assert jsonable_cell(float("nan")) is None
    assert jsonable_cell(float("inf")) is None


def test_jsonable_row_round_trip() -> None:
    row = {
        "d": date(2025, 12, 25),
        "amt": Decimal("10.5"),
        "meta": {"ts": datetime(2025, 1, 1, 0, 0, 0)},
    }
    safe = jsonable_row(row)
    json.dumps(safe)
    assert safe["d"] == "2025-12-25"
    assert safe["amt"] == 10.5
    assert safe["meta"]["ts"] == "2025-01-01T00:00:00"
