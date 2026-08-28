# Data

The raw Olist CSVs are **not** committed to keep the repo light. Get them yourself:

## Option A — Kaggle website
1. Go to <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>
2. Download the ZIP and unzip **all CSVs** into `data/raw/`.

## Option B — Kaggle CLI
```bash
pip install kaggle
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
```

## Expected files in `data/raw/`
```
olist_customers_dataset.csv
olist_orders_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
olist_geolocation_dataset.csv
product_category_name_translation.csv
```

Then build the database:
```bash
python src/build_db.py
```
