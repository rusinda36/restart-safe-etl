
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import hashlib

import pyodbc
from openpyxl import load_workbook


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / "data" / "raw" / "online_retail_II.xlsx"

SERVER = r".\SQLEXPRESS"
DATABASE = "RestartSafeETL"

BATCH_SIZE = 1000

# First experiment: fail before committing batch 6.
FAIL_BEFORE_COMMIT_AT_BATCH = None

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)


def calculate_hash(path):
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def normalize(value):
    if value is None:
        return None

    if isinstance(value, str):
        return value

    return str(value)


def prepare_record(source_file_id, sheet_name, row_number, row):
    (
        invoice,
        stock_code,
        description,
        quantity,
        invoice_date,
        price,
        customer_id,
        country
    ) = row

    return (
        source_file_id,
        sheet_name,
        row_number,
        normalize(invoice),
        normalize(stock_code),
        normalize(description),
        int(quantity) if quantity is not None else None,
        invoice_date,
        Decimal(str(price)) if price is not None else None,
        normalize(customer_id),
        normalize(country)
    )


def process_batch(
    connection,
    source_file_id,
    sheet_name,
    records,
    batch_number
):
    start_row = records[0][2]
    end_row = records[-1][2]

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT Status
            FROM etl.LoadBatch
            WHERE SourceFileID = ?
              AND SourceSheet = ?
              AND StartRowNumber = ?
              AND EndRowNumber = ?
            """,
            source_file_id,
            sheet_name,
            start_row,
            end_row
        )

        existing = cursor.fetchone()

        if existing is not None and existing[0] == "Completed":
            print(
                f"SKIPPED batch {batch_number}: "
                f"rows {start_row}-{end_row}"
            )
            return

        if existing is not None:
            raise RuntimeError(
                f"Batch {batch_number} has unexpected "
                f"status: {existing[0]}"
            )

        cursor.executemany(
            """
            INSERT INTO stg.RetailTransaction (
                SourceFileID,
                SourceSheet,
                SourceRowNumber,
                Invoice,
                StockCode,
                Description,
                Quantity,
                InvoiceDate,
                Price,
                CustomerID,
                Country
            )
            SELECT
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM stg.RetailTransaction WITH (UPDLOCK, HOLDLOCK)
                WHERE SourceFileID = ?
                  AND SourceSheet = ?
                  AND SourceRowNumber = ?
            )
            """,
            [
                record + (record[0], record[1], record[2])
                for record in records
            ]
        )

        cursor.execute(
            """
            INSERT INTO etl.LoadBatch (
                SourceFileID,
                SourceSheet,
                StartRowNumber,
                EndRowNumber,
                Status,
                RowsLoaded,
                CompletedAt
            )
            VALUES (?, ?, ?, ?, 'Completed', ?, SYSUTCDATETIME())
            """,
            source_file_id,
            sheet_name,
            start_row,
            end_row,
            len(records)
        )

        if batch_number == FAIL_BEFORE_COMMIT_AT_BATCH:
            print(
                f"\nSIMULATED FAILURE before COMMIT "
                f"for batch {batch_number}"
            )
            raise RuntimeError("Simulated ETL crash")

        connection.commit()

        print(
            f"COMMITTED batch {batch_number}: "
            f"rows {start_row}-{end_row}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()


def main():
    file_hash = calculate_hash(SOURCE_FILE)

    connection = pyodbc.connect(
        connection_string,
        autocommit=False
    )

    workbook = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT SourceFileID
            FROM etl.SourceFile
            WHERE FileHash = ?
            """,
            file_hash
        )

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                "Source file must be registered first."
            )

        source_file_id = result[0]
        cursor.close()

        print(f"SourceFileID: {source_file_id}")

        workbook = load_workbook(
            SOURCE_FILE,
            read_only=True,
            data_only=True
        )

        batch_number = 0

        for worksheet in workbook.worksheets:
            sheet_name = worksheet.title
            print(f"\nProcessing worksheet: {sheet_name}")

            records = []

            for row_number, row in enumerate(
                worksheet.iter_rows(
                    min_row=2,
                    values_only=True
                ),
                start=2
            ):
                records.append(
                    prepare_record(
                        source_file_id,
                        sheet_name,
                        row_number,
                        row
                    )
                )

                if len(records) == BATCH_SIZE:
                    batch_number += 1

                    process_batch(
                        connection,
                        source_file_id,
                        sheet_name,
                        records,
                        batch_number
                    )

                    records = []

            if records:
                batch_number += 1

                process_batch(
                    connection,
                    source_file_id,
                    sheet_name,
                    records,
                    batch_number
                )

        print("\nETL completed successfully.")

    finally:
        if workbook is not None:
            workbook.close()

        connection.close()


if __name__ == "__main__":
    main()
