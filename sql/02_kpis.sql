-- 02_kpis.sql
-- Headline business KPIs. Run any block on its own.

-- Monthly revenue, orders, and average order value ------------------------
SELECT
    purchase_month,
    COUNT(DISTINCT order_id)                                   AS orders,
    ROUND(SUM(gross_revenue), 2)                               AS revenue,
    ROUND(SUM(gross_revenue) / COUNT(DISTINCT order_id), 2)    AS avg_order_value
FROM fct_order_items
GROUP BY purchase_month
ORDER BY purchase_month;

-- Top 10 product categories by revenue ------------------------------------
SELECT
    category,
    ROUND(SUM(gross_revenue), 2)  AS revenue,
    COUNT(DISTINCT order_id)      AS orders
FROM fct_order_items
GROUP BY category
ORDER BY revenue DESC
LIMIT 10;

-- Revenue and customers by state ------------------------------------------
SELECT
    customer_state,
    ROUND(SUM(gross_revenue), 2)          AS revenue,
    COUNT(DISTINCT customer_unique_id)    AS customers
FROM fct_order_items
GROUP BY customer_state
ORDER BY revenue DESC;

-- One-time vs. repeat customers (the retention headline) ------------------
WITH per_customer AS (
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS orders
    FROM fct_order_items
    GROUP BY customer_unique_id
)
SELECT
    CASE WHEN orders = 1 THEN 'one-time' ELSE 'repeat' END AS customer_type,
    COUNT(*)                                               AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)     AS pct
FROM per_customer
GROUP BY customer_type;
