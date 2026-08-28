-- 04_cohort_retention.sql
-- Monthly acquisition cohorts and their repeat-purchase activity over time.
-- Output pivots into the classic retention heatmap (cohort_month x month_offset).

WITH first_purchase AS (
    SELECT
        customer_unique_id,
        DATE_TRUNC('month', MIN(purchase_ts)) AS cohort_month
    FROM fct_order_items
    GROUP BY customer_unique_id
),
activity AS (
    SELECT DISTINCT
        f.customer_unique_id,
        fp.cohort_month,
        DATE_DIFF('month', fp.cohort_month,
                  DATE_TRUNC('month', f.purchase_ts)) AS month_offset
    FROM fct_order_items f
    JOIN first_purchase fp USING (customer_unique_id)
)
SELECT
    cohort_month,
    month_offset,
    COUNT(DISTINCT customer_unique_id) AS customers
FROM activity
GROUP BY cohort_month, month_offset
ORDER BY cohort_month, month_offset;
