-- 01_cleaning.sql
-- One clean, analysis-ready fact view at the order-item grain.
-- Scope: delivered orders, positive item price. Enriched with the real customer
-- identity (customer_unique_id) and the English category name.

CREATE OR REPLACE VIEW fct_order_items AS
SELECT
    oi.order_id,
    oi.order_item_id,
    o.customer_id,
    c.customer_unique_id,                                   -- real customer across orders
    c.customer_state,
    oi.product_id,
    COALESCE(t.product_category_name_english,
             p.product_category_name, 'unknown')     AS category,
    o.order_status,
    CAST(o.order_purchase_timestamp AS TIMESTAMP)    AS purchase_ts,
    DATE_TRUNC('month',
        CAST(o.order_purchase_timestamp AS TIMESTAMP)) AS purchase_month,
    -- delivery time in days (NULL if not delivered)
    DATE_DIFF('day',
        CAST(o.order_purchase_timestamp AS TIMESTAMP),
        CAST(o.order_delivered_customer_date AS TIMESTAMP)) AS delivery_days,
    oi.price,
    oi.freight_value,
    (oi.price + oi.freight_value)                    AS gross_revenue
FROM order_items oi
JOIN orders o             ON oi.order_id = o.order_id
JOIN customers c          ON o.customer_id = c.customer_id
LEFT JOIN products p      ON oi.product_id = p.product_id
LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
  AND oi.price > 0;
