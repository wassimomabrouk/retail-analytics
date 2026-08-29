"""
Export the Olist star schema for the Power BI rebuild.

Reads the existing DuckDB pipeline (the single source of truth, so the Power BI
figures match the published Tableau dashboard exactly) and writes Power BI-ready
CSVs into powerbi/data/:

    fct_order_items.csv    fact  -- one row per delivered order-item
    dim_date.csv           dim   -- calendar table (unlocks time-intelligence DAX)
    dim_customer.csv       dim   -- one row per customer_unique_id
    dim_product.csv        dim   -- one row per product_id (+ English category)
    dim_geography.csv      dim   -- one row per state (+ centroid lat/long for the map)
    cohort_retention.csv   fact  -- long-format monthly retention (recomputed from source)

Run from the repo root:

    py powerbi/export_star_schema.py
"""

from pathlib import Path
import glob
import sys

import duckdb
import pandas as pd

# --- locate the DuckDB file -------------------------------------------------
REPO = Path(__file__).resolve().parent.parent
db_candidates = glob.glob(str(REPO / "**" / "*.duckdb"), recursive=True)
if not db_candidates:
    sys.exit("No .duckdb file found under the repo.")
DB_PATH = db_candidates[0]
print(f"Using DuckDB: {DB_PATH}")

OUT = REPO / "powerbi" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# read-only so it won't clash with an open notebook connection
con = duckdb.connect(DB_PATH, read_only=True)
df = con.execute("SELECT * FROM fct_order_items").fetchdf()
print(f"fct_order_items: {df.shape[0]:,} rows")

# --- fact: one row per delivered order-item (atomic grain) ------------------
fact = pd.DataFrame({
    "order_id":           df["order_id"],
    "order_date":         pd.to_datetime(df["purchase_ts"]).dt.date,
    "customer_unique_id": df["customer_unique_id"],
    "product_id":         df["product_id"],
    "state":              df["customer_state"],
    "price":              df["price"],
    "freight_value":      df["freight_value"],
    "revenue":            df["gross_revenue"],   # source-of-truth revenue = matches Tableau
    "delivery_days":      df["delivery_days"],
})
fact.to_csv(OUT / "fct_order_items.csv", index=False)
print(f"fct_order_items.csv   {len(fact):,} rows")

# --- dim_date: full calendar over the fact's date range ---------------------
dmin = pd.to_datetime(fact["order_date"]).min()
dmax = pd.to_datetime(fact["order_date"]).max()
dim_date = pd.DataFrame({"Date": pd.date_range(dmin, dmax, freq="D")})
dim_date["Year"]      = dim_date["Date"].dt.year
dim_date["Quarter"]   = "Q" + dim_date["Date"].dt.quarter.astype(str)
dim_date["MonthNo"]   = dim_date["Date"].dt.month
dim_date["Month"]     = dim_date["Date"].dt.strftime("%b")
dim_date["YearMonth"] = dim_date["Date"].dt.strftime("%Y-%m")
dim_date["Date"]      = dim_date["Date"].dt.date
dim_date.to_csv(OUT / "dim_date.csv", index=False)
print(f"dim_date.csv          {len(dim_date):,} rows ({dmin.date()} to {dmax.date()})")

# --- dim_customer: one row per customer_unique_id ---------------------------
dim_customer = (df[["customer_unique_id", "customer_state"]]
                .drop_duplicates(subset=["customer_unique_id"])
                .rename(columns={"customer_state": "state"}))
dim_customer.to_csv(OUT / "dim_customer.csv", index=False)
print(f"dim_customer.csv      {len(dim_customer):,} rows")

# --- dim_product: one row per product_id (+ English category) ---------------
dim_product = df[["product_id", "category"]].drop_duplicates(subset=["product_id"])
dim_product.to_csv(OUT / "dim_product.csv", index=False)
print(f"dim_product.csv       {len(dim_product):,} rows")

# --- dim_geography: Brazilian state centroids (geocode-free map) -------------
BR_CENTROIDS = {
    "AC": (-9.02, -70.81),  "AL": (-9.57, -36.55),  "AP": (1.41, -51.77),
    "AM": (-3.47, -65.10),  "BA": (-12.96, -41.71), "CE": (-5.20, -39.53),
    "DF": (-15.83, -47.86), "ES": (-19.19, -40.34), "GO": (-15.98, -49.86),
    "MA": (-5.42, -45.44),  "MT": (-12.64, -55.42), "MS": (-20.51, -54.54),
    "MG": (-18.10, -44.38), "PA": (-3.79, -52.48),  "PB": (-7.28, -36.72),
    "PR": (-24.89, -51.55), "PE": (-8.38, -37.86),  "PI": (-6.60, -42.28),
    "RJ": (-22.25, -42.66), "RN": (-5.81, -36.59),  "RS": (-30.17, -53.50),
    "RO": (-10.83, -63.34), "RR": (1.99, -61.33),   "SC": (-27.45, -50.95),
    "SP": (-22.19, -48.79), "SE": (-10.57, -37.45), "TO": (-9.46, -48.26),
}
states = sorted(s for s in fact["state"].dropna().unique())
dim_geo = pd.DataFrame([{"state": s,
                         "lat": BR_CENTROIDS.get(s, (None, None))[0],
                         "lon": BR_CENTROIDS.get(s, (None, None))[1]} for s in states])
dim_geo.to_csv(OUT / "dim_geography.csv", index=False)
print(f"dim_geography.csv     {len(dim_geo):,} rows")

# --- cohort retention: recomputed from source (no cohort table in the DB) ---
# Monthly customer retention: cohort = month of a customer's first delivered order.
cust = fact[["customer_unique_id", "order_date"]].copy()
cust["order_month"] = pd.to_datetime(cust["order_date"]).dt.to_period("M")
first = cust.groupby("customer_unique_id")["order_month"].min().rename("cohort_month")
cust = cust.join(first, on="customer_unique_id")
cust["months_since"] = ((cust["order_month"].dt.year - cust["cohort_month"].dt.year) * 12
                        + (cust["order_month"].dt.month - cust["cohort_month"].dt.month))

cohort_size = (first.reset_index()
               .groupby("cohort_month")["customer_unique_id"].nunique()
               .rename("cohort_size"))
cohort = (cust.groupby(["cohort_month", "months_since"])["customer_unique_id"]
          .nunique().rename("active_customers").reset_index()
          .join(cohort_size, on="cohort_month"))
cohort["retention_pct"] = (cohort["active_customers"] / cohort["cohort_size"] * 100).round(2)

# 2017-01 onward: early cohorts are n~1 and produce misleading 100% artifacts
cohort = cohort[cohort["cohort_month"] >= pd.Period("2017-01", "M")]
cohort["cohort_month"] = cohort["cohort_month"].astype(str)
cohort = cohort.sort_values(["cohort_month", "months_since"])
cohort.to_csv(OUT / "cohort_retention.csv", index=False)
print(f"cohort_retention.csv  {len(cohort):,} rows")

con.close()
print(f"\nDone. CSVs written to: {OUT}")
