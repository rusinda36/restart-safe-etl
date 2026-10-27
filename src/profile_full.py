
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"

if not SOURCE_FILE.is_file():
    raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

with pd.ExcelFile(SOURCE_FILE, engine="openpyxl") as workbook:
    for sheet_name in workbook.sheet_names:

        print(f"\n{'=' * 60}")
        print(f"WORKSHEET: {sheet_name}")
        print("=" * 60)

        df = pd.read_excel(workbook, sheet_name=sheet_name)

        print(f"Total rows: {len(df):,}")
        print(f"Total columns: {len(df.columns)}")

        print("\nDATA TYPES:")
        print(df.dtypes.to_string())

        print("\nNULL VALUES:")
        print(df.isna().sum().to_string())

        print("\nFULLY DUPLICATED ROWS:")
        print(f"{df.duplicated().sum():,}")

        print("\nINVOICE ANALYSIS:")
        print(f"Unique invoices: {df['Invoice'].nunique():,}")

        print("\nQUANTITY ANALYSIS:")
        print(f"Negative quantities: {(df['Quantity'] < 0).sum():,}")
        print(f"Zero quantities: {(df['Quantity'] == 0).sum():,}")

        print("\nPRICE ANALYSIS:")
        print(f"Negative prices: {(df['Price'] < 0).sum():,}")
        print(f"Zero prices: {(df['Price'] == 0).sum():,}")

        print("\nDATE RANGE:")
        print(f"Minimum: {df['InvoiceDate'].min()}")
        print(f"Maximum: {df['InvoiceDate'].max()}")

        del df
