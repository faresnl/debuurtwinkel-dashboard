"""Check the data files locally before a cloud deployment."""
import csv
from pathlib import Path

folder = Path(__file__).resolve().parent / "data"
requirements = {
    "sales_data.csv": {"TransactionID", "Date", "ProductID", "StoreID", "UnitsSold"},
    "product_details.csv": {"ProductID", "ProductName", "ProductCategory", "UnitPrice", "UnitCost"},
    "store_locations.csv": {"StoreID", "City", "Province"},
}
all_good = True
for filename, fields in requirements.items():
    path = folder / filename
    if not path.is_file():
        print(f"MISSING {path}")
        all_good = False
        continue
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            actual = set(reader.fieldnames or [])
        missing = fields - actual
        if missing:
            print(f"CHECK {filename}: missing columns {', '.join(sorted(missing))}")
            all_good = False
        else:
            print(f"OK {filename}")
    except UnicodeDecodeError:
        # App also supports Windows-1252 source CSVs.
        with path.open(encoding="cp1252", newline="") as file:
            actual = set(csv.DictReader(file).fieldnames or [])
        missing = fields - actual
        if missing:
            print(f"CHECK {filename}: missing columns {', '.join(sorted(missing))}")
            all_good = False
        else:
            print(f"OK {filename}")
print("All data files look ready." if all_good else "Fix missing data before deploying.")
raise SystemExit(0 if all_good else 1)
