
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import hashlib
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from load_transactions import (
    calculate_hash,
    normalize,
    prepare_record,
)


def test_calculate_hash(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"restart-safe-etl")

    expected = hashlib.sha256(b"restart-safe-etl").hexdigest()

    assert calculate_hash(source) == expected


def test_normalize_none():
    assert normalize(None) is None


def test_normalize_string():
    assert normalize("INV-100") == "INV-100"


def test_normalize_number():
    assert normalize(12345) == "12345"


def test_prepare_record():
    invoice_date = datetime(2010, 5, 12, 14, 30)

    source_row = (
        "INV-100",
        "SKU-001",
        "Example product",
        3,
        invoice_date,
        12.3456,
        12345,
        "United Kingdom",
    )

    result = prepare_record(
        source_file_id=1,
        sheet_name="Year 2009-2010",
        row_number=2,
        row=source_row,
    )

    assert result == (
        1,
        "Year 2009-2010",
        2,
        "INV-100",
        "SKU-001",
        "Example product",
        3,
        invoice_date,
        Decimal("12.3456"),
        "12345",
        "United Kingdom",
    )


def test_prepare_record_with_nulls():
    source_row = (
        None,
        "SKU-002",
        None,
        None,
        None,
        None,
        None,
        "Canada",
    )

    result = prepare_record(
        source_file_id=1,
        sheet_name="Year 2009-2010",
        row_number=3,
        row=source_row,
    )

    assert result[3] is None
    assert result[5] is None
    assert result[6] is None
    assert result[7] is None
    assert result[8] is None
    assert result[9] is None
    assert result[10] == "Canada"


@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 5),
        (-3, -3),
        (0, 0),
    ],
)
def test_prepare_record_quantity(quantity, expected):
    source_row = (
        "INV-200",
        "SKU-003",
        "Test product",
        quantity,
        datetime(2010, 1, 1),
        9.99,
        None,
        "Canada",
    )

    result = prepare_record(1, "Year 2009-2010", 10, source_row)

    assert result[6] == expected
