from pathlib import Path
import hashlib
import pyodbc

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / "data" / "raw" / "online_retail_II.xlsx"

SERVER = r".\SQLEXPRESS"
DATABASE = "RestartSafeETL"


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


if not SOURCE_FILE.is_file():
    raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

file_hash = calculate_sha256(SOURCE_FILE)
file_size = SOURCE_FILE.stat().st_size

print(f"File: {SOURCE_FILE.name}")
print(f"Size: {file_size:,} bytes")
print(f"SHA-256: {file_hash}")

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

with pyodbc.connect(connection_string) as connection:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT SourceFileID
        FROM etl.SourceFile
        WHERE FileHash = ?
        """,
        file_hash
    )

    existing = cursor.fetchone()

    if existing:
        source_file_id = existing[0]
        print(f"File already registered. SourceFileID: {source_file_id}")

    else:
        try:
            cursor.execute(
                """
                INSERT INTO etl.SourceFile
                    (FileName, FileHash, FileSizeBytes, RegisteredAt)
                VALUES
                    (?, ?, ?, SYSUTCDATETIME())
                """,
                SOURCE_FILE.name,
                file_hash,
                file_size
            )

            cursor.execute(
                """
                SELECT SourceFileID
                FROM etl.SourceFile
                WHERE FileHash = ?
                """,
                file_hash
            )

            source_file_id = cursor.fetchone()[0]
            connection.commit()

            print(f"File registered. SourceFileID: {source_file_id}")

        except Exception:
            connection.rollback()
            raise