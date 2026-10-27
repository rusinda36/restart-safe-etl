
from pathlib import Path
from unittest.mock import MagicMock
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import load_transactions as loader


@pytest.fixture
def connection():
    conn = MagicMock()
    conn.cursor.return_value.fetchone.return_value = None
    return conn


@pytest.fixture
def records():
    return [
        (
            1, "Year 2009-2010", 2,
            "INV-001", "SKU-001", "Product A",
            2, None, None, None, "Canada"
        ),
        (
            1, "Year 2009-2010", 3,
            "INV-002", "SKU-002", "Product B",
            1, None, None, None, "Canada"
        ),
    ]


def test_new_batch_commits(connection, records, monkeypatch):
    monkeypatch.setattr(
        loader, "FAIL_BEFORE_COMMIT_AT_BATCH", None
    )

    loader.process_batch(
        connection, 1, "Year 2009-2010", records, 1
    )

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    connection.cursor.return_value.executemany.assert_called_once()
    connection.cursor.return_value.close.assert_called_once()


def test_completed_batch_is_skipped(connection, records):
    cursor = connection.cursor.return_value
    cursor.fetchone.return_value = ("Completed",)

    loader.process_batch(
        connection, 1, "Year 2009-2010", records, 1
    )

    cursor.executemany.assert_not_called()
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()


def test_unexpected_status_rolls_back(connection, records):
    cursor = connection.cursor.return_value
    cursor.fetchone.return_value = ("Started",)

    with pytest.raises(RuntimeError, match="unexpected status"):
        loader.process_batch(
            connection, 1, "Year 2009-2010", records, 1
        )

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    cursor.close.assert_called_once()


def test_simulated_failure_rolls_back(
    connection, records, monkeypatch
):
    monkeypatch.setattr(
        loader, "FAIL_BEFORE_COMMIT_AT_BATCH", 6
    )

    with pytest.raises(RuntimeError, match="Simulated ETL crash"):
        loader.process_batch(
            connection, 1, "Year 2009-2010", records, 6
        )

    connection.cursor.return_value.executemany.assert_called_once()
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.cursor.return_value.close.assert_called_once()


def test_insert_failure_rolls_back(connection, records, monkeypatch):
    monkeypatch.setattr(
        loader, "FAIL_BEFORE_COMMIT_AT_BATCH", None
    )

    cursor = connection.cursor.return_value
    cursor.executemany.side_effect = RuntimeError("Insert failed")

    with pytest.raises(RuntimeError, match="Insert failed"):
        loader.process_batch(
            connection, 1, "Year 2009-2010", records, 1
        )

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    cursor.close.assert_called_once()
