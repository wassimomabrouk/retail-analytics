"""Build the analytics DuckDB from raw Olist CSVs and materialize the clean fact view.

Usage:
    python src/build_db.py
"""
from pathlib import Path
import duckdb

DB_PATH = "data/olist.duckdb"
SQL_DIR = Path("sql")
STEPS = ["00_load.sql", "01_cleaning.sql"]


def main() -> None:
    con = duckdb.connect(DB_PATH)
    for step in STEPS:
        print(f"Running {step} ...")
        con.execute((SQL_DIR / step).read_text())
    rows = con.execute("SELECT COUNT(*) FROM fct_order_items").fetchone()[0]
    print(f"\nDone -> {DB_PATH}")
    print(f"fct_order_items: {rows:,} rows")
    con.close()


if __name__ == "__main__":
    main()
