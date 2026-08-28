-- 03_rfm.sql
-- RFM segmentation per real customer (customer_unique_id).
-- Recency = days since last purchase, Frequency = # orders, Monetary = total spend.
-- Each dimension is scored 1–5 with NTILE, then mapped to a business segment.

WITH bounds AS (
    SELECT MAX(purchase_ts) + INTERVAL 1 DAY AS as_of
    FROM fct_order_items
),
customer_rfm AS (
    SELECT
        f.customer_unique_id,
        DATE_DIFF('day', MAX(f.purchase_ts), b.as_of) AS recency_days,
        COUNT(DISTINCT f.order_id)                    AS frequency,
        ROUND(SUM(f.gross_revenue), 2)                AS monetary
    FROM fct_order_items f
    CROSS JOIN bounds b
    GROUP BY f.customer_unique_id, b.as_of
),
scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,  -- more recent = higher
        NTILE(5) OVER (ORDER BY frequency)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary)          AS m_score
    FROM customer_rfm
)
SELECT *,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New / Promising'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
        ELSE 'Needs Attention'
    END AS segment
FROM scored
ORDER BY monetary DESC;
