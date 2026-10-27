
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"

with pd.ExcelFile(SOURCE_FILE, engine="openpyxl") as workbook:
    for sheet_name in workbook.sheet_names:

        df = pd.read_excel(workbook, sheet_name=sheet_name)

        print(f"\n{'=' * 60}")
        print(f"WORKSHEET: {sheet_name}")
        print("=" * 60)

        # Convert Invoice to string for prefix analysis
        invoice = df["Invoice"].astype("string")

        # Identify cancellation-marked invoices
        cancellation = invoice.str.startswith("C", na=False)

        # Identify negative quantities
        negative_qty = df["Quantity"] < 0

        print(f"Total rows: {len(df):,}")
        print(f"Cancellation-marked rows: {cancellation.sum():,}")
        print(f"Negative quantity rows: {negative_qty.sum():,}")

        print("\nCANCELLATION VS NEGATIVE QUANTITY:")
        print(
            pd.crosstab(
                cancellation,
                negative_qty,
                rownames=["Invoice starts with C"],
                colnames=["Quantity < 0"]
            )
        )

        print("\nNEGATIVE QUANTITY WITHOUT C PREFIX:")
        exceptions = df.loc[
            negative_qty & ~cancellation,
            ["Invoice", "StockCode", "Quantity", "Price"]
        ]

        print(f"Count: {len(exceptions):,}")
        print(exceptions.head(10).to_string(index=False))

        print("\nC PREFIX WITHOUT NEGATIVE QUANTITY:")
        reverse_exceptions = df.loc[
            cancellation & ~negative_qty,
            ["Invoice", "StockCode", "Quantity", "Price"]
        ]

        print(f"Count: {len(reverse_exceptions):,}")
        print(reverse_exceptions.head(10).to_string(index=False))

        del df
