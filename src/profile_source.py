
from pathlib import Path
import pandas as pd

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Original source file
SOURCE_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"

# Verify that the source file exists
if not SOURCE_FILE.is_file():
    raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

# Inspect workbook structure without loading all records
workbook = pd.ExcelFile(SOURCE_FILE, engine="openpyxl")

print("SOURCE DATA PROFILING")
print("=" * 50)
print(f"Source file: {SOURCE_FILE.name}")
print(f"File size: {SOURCE_FILE.stat().st_size:,} bytes")
print(f"Worksheets: {workbook.sheet_names}")

# Inspect the first five rows of each worksheet
for sheet_name in workbook.sheet_names:
    print(f"\nWORKSHEET: {sheet_name}")
    print("-" * 50)

    sample = pd.read_excel(
        workbook,
        sheet_name=sheet_name,
        nrows=5
    )

    print(f"Columns: {sample.columns.tolist()}")
    print("\nSample records:")
    print(sample.to_string(index=False))

workbook.close()
 