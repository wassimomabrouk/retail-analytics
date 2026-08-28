-- 00_load.sql
-- Load raw Olist CSVs into DuckDB tables. Run from the repo root.
-- read_csv_auto infers types and handles the header row.

CREATE OR REPLACE TABLE customers           AS SELECT * FROM read_csv_auto('data/raw/olist_customers_dataset.csv');
CREATE OR REPLACE TABLE orders              AS SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv');
CREATE OR REPLACE TABLE order_items         AS SELECT * FROM read_csv_auto('data/raw/olist_order_items_dataset.csv');
CREATE OR REPLACE TABLE payments            AS SELECT * FROM read_csv_auto('data/raw/olist_order_payments_dataset.csv');
CREATE OR REPLACE TABLE reviews             AS SELECT * FROM read_csv_auto('data/raw/olist_order_reviews_dataset.csv');
CREATE OR REPLACE TABLE products            AS SELECT * FROM read_csv_auto('data/raw/olist_products_dataset.csv');
CREATE OR REPLACE TABLE sellers             AS SELECT * FROM read_csv_auto('data/raw/olist_sellers_dataset.csv');
CREATE OR REPLACE TABLE category_translation AS SELECT * FROM read_csv_auto('data/raw/product_category_name_translation.csv');
