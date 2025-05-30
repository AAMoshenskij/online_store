-- Top Sellers Dashboard
SELECT 
    s.first_name,
    s.last_name,
    count() as total_orders,
    sum(oi.quantity) as total_items_sold,
    sum(oi.quantity * p.external_price) as total_revenue
FROM online_store.orders o
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.sellers s ON oi.seller_id = s.seller_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH
GROUP BY s.first_name, s.last_name
ORDER BY total_revenue DESC
LIMIT 10;

-- Top Categories Dashboard
SELECT 
    p.main_category,
    count() as total_orders,
    sum(oi.quantity) as total_quantity_sold,
    sum(oi.quantity * p.external_price) as total_revenue
FROM online_store.orders o
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH
GROUP BY p.main_category
ORDER BY total_revenue DESC;

-- Customer Demographics Dashboard
SELECT 
    avg(u.user_age) as average_age,
    count(DISTINCT o.user_id) as total_customers,
    sum(oi.quantity * p.external_price) / count(DISTINCT o.user_id) as average_spend,
    count(DISTINCT CASE WHEN u.user_age < 25 THEN o.user_id END) as under_25,
    count(DISTINCT CASE WHEN u.user_age BETWEEN 25 AND 35 THEN o.user_id END) as age_25_35,
    count(DISTINCT CASE WHEN u.user_age BETWEEN 36 AND 45 THEN o.user_id END) as age_36_45,
    count(DISTINCT CASE WHEN u.user_age > 45 THEN o.user_id END) as over_45
FROM online_store.orders o
JOIN online_store.users u ON o.user_id = u.user_id
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH;

-- Sales Metrics Dashboard
SELECT 
    toStartOfDay(o.order_date) as time,
    count() as total_orders,
    sum(oi.quantity) as total_items_sold,
    sum(oi.quantity * p.external_price) as total_revenue,
    avg(oi.quantity * p.external_price) as average_order_value
FROM online_store.orders o
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH
GROUP BY time
ORDER BY time;

-- Product Performance Dashboard
SELECT 
    p.product_name,
    p.main_category,
    count() as total_orders,
    sum(oi.quantity) as total_quantity_sold,
    sum(oi.quantity * p.external_price) as total_revenue
FROM online_store.orders o
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH
GROUP BY p.product_name, p.main_category
ORDER BY total_revenue DESC
LIMIT 10;

-- Daily Sales Trend
SELECT 
    toStartOfDay(o.order_date) as time,
    sum(oi.quantity * p.external_price) as daily_revenue,
    count() as daily_orders,
    sum(oi.quantity) as daily_items_sold
FROM online_store.orders o
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH
GROUP BY time
ORDER BY time;

-- Category Distribution
SELECT 
    p.main_category,
    count(DISTINCT o.order_id) as order_count,
    sum(oi.quantity) as items_sold,
    sum(oi.quantity * p.external_price) as category_revenue,
    sum(oi.quantity * p.external_price) / sum(sum(oi.quantity * p.external_price)) OVER () * 100 as revenue_percentage
FROM online_store.orders o
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH
GROUP BY p.main_category
ORDER BY category_revenue DESC;

-- Customer Age Distribution
SELECT 
    CASE 
        WHEN u.user_age < 25 THEN 'Under 25'
        WHEN u.user_age BETWEEN 25 AND 35 THEN '25-35'
        WHEN u.user_age BETWEEN 36 AND 45 THEN '36-45'
        ELSE 'Over 45'
    END as age_group,
    count(DISTINCT o.user_id) as customer_count,
    sum(oi.quantity * p.external_price) as group_revenue,
    avg(oi.quantity * p.external_price) as average_spend
FROM online_store.orders o
JOIN online_store.users u ON o.user_id = u.user_id
JOIN online_store.order_items oi ON o.order_id = oi.order_id
JOIN online_store.products p ON oi.product_id = p.product_id
WHERE o.order_date >= now() - INTERVAL 1 MONTH
GROUP BY age_group
ORDER BY customer_count DESC; 