-- Create database
CREATE DATABASE IF NOT EXISTS online_store;

USE online_store;

CREATE TABLE IF NOT EXISTS users (
    user_id UInt32,
    user_age UInt8,
    first_name String,
    last_name String,
    is_verified_email Boolean,
    is_active Boolean,
    date_joined DateTime,
    last_login DateTime,

    etl_updated_at DateTime DEFAULT NOW()
) ENGINE = ReplacingMergeTree(etl_updated_at)
ORDER BY (user_id);


CREATE TABLE IF NOT EXISTS sellers (
    seller_id UInt32,
    first_name String,
    last_name String,
    -- -- Additional seller attributes for analytics
    -- seller_rating Float32,
    -- seller_category String,
    -- seller_region String,
    -- seller_city String,
    -- seller_country String,
    -- total_products UInt32,

    etl_updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(etl_updated_at)
ORDER BY (seller_id);


CREATE TABLE IF NOT EXISTS products (
    product_id UInt32,
    product_name String,
    main_category String,
    sub_category String,
    external_ratings Float32,
    external_ratings_count UInt32,
    -- цена в беке, почему-то, строка <?> 
    external_price Decimal(10, 2),
    
    etl_updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(etl_updated_at)
ORDER BY (product_id);

CREATE TABLE IF NOT EXISTS order_items (
    order_id UInt32,
    product_id UInt32,
    seller_id UInt32,
    quantity UInt32,
    -- price Decimal(10,2),
    -- total_price Decimal(10,2),
    -- Additional metrics
    -- discount_amount Decimal(10,2) DEFAULT 0,
    -- tax_amount Decimal(10,2) DEFAULT 0,
    -- shipping_amount Decimal(10,2) DEFAULT 0,
    etl_updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(etl_updated_at)
ORDER BY (order_id);


CREATE TABLE IF NOT EXISTS payments (
    order_id UInt32,
    amount Decimal(10, 2),
    currency String,
    status String,
    payment_method String,
    created_at DateTime,
    etl_updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(etl_updated_at)
ORDER BY (order_id);


CREATE TABLE IF NOT EXISTS orders (
    order_id UInt32,
    order_date Date,
    user_id UInt32,
    status String,
    -- Metadata
    etl_updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(etl_updated_at)
ORDER BY (order_id, order_date);




-- Dashboard Analytics Views

-- Top Sellers by Revenue and Sales
-- CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_sellers_revenue
-- ENGINE = ReplacingMergeTree(etl_updated_at)
-- ORDER BY (etl_updated_at, month)
-- SETTINGS index_granularity = 8192
-- AS
-- SELECT
--     now() as etl_updated_at,
--     toStartOfMonth(o.order_date) as month,
--     oi.seller_id,
--     s.first_name as seller_first_name,
--     s.last_name as seller_last_name,
--     count() as total_orders,
--     sum(oi.quantity) as total_items_sold,
--     count(DISTINCT o.user_id) as unique_customers,
--     sum(oi.quantity * p.external_price) as total_revenue,
--     avg(oi.quantity * p.external_price) as average_order_value
-- FROM orders o
-- JOIN order_items oi ON o.order_id = oi.order_id
-- JOIN sellers s ON oi.seller_id = s.seller_id
-- JOIN products p ON oi.product_id = p.product_id
-- WHERE o.order_date >= toStartOfMonth(now()) - INTERVAL 1 MONTH
-- GROUP BY month, oi.seller_id, s.first_name, s.last_name;

-- -- Top Categories by Sales and Revenue
-- CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_categories
-- ENGINE = ReplacingMergeTree(etl_updated_at)
-- ORDER BY (etl_updated_at, month)
-- SETTINGS index_granularity = 8192
-- AS
-- SELECT
--     now() as etl_updated_at,
--     toStartOfMonth(o.order_date) as month,
--     p.main_category,
--     count() as total_orders,
--     sum(oi.quantity) as total_quantity_sold,
--     count(DISTINCT o.user_id) as unique_customers,
--     sum(oi.quantity * p.external_price) as total_revenue,
--     avg(oi.quantity * p.external_price) as average_order_value
-- FROM orders o
-- JOIN order_items oi ON o.order_id = oi.order_id
-- JOIN products p ON oi.product_id = p.product_id
-- WHERE o.order_date >= toStartOfMonth(now()) - INTERVAL 1 MONTH
-- GROUP BY month, p.main_category;

-- -- Customer Demographics and Spending
-- CREATE MATERIALIZED VIEW IF NOT EXISTS mv_customer_demographics
-- ENGINE = ReplacingMergeTree(etl_updated_at)
-- ORDER BY (etl_updated_at, month)
-- SETTINGS index_granularity = 8192
-- AS
-- SELECT
--     now() as etl_updated_at,
--     toStartOfMonth(o.order_date) as month,
--     avg(u.user_age) as average_customer_age,
--     count(DISTINCT o.user_id) as total_customers,
--     sum(oi.quantity * p.external_price) / count(DISTINCT o.user_id) as average_customer_spend,
--     count(DISTINCT CASE WHEN u.user_age < 25 THEN o.user_id END) as customers_under_25,
--     count(DISTINCT CASE WHEN u.user_age BETWEEN 25 AND 35 THEN o.user_id END) as customers_25_35,
--     count(DISTINCT CASE WHEN u.user_age BETWEEN 36 AND 45 THEN o.user_id END) as customers_36_45,
--     count(DISTINCT CASE WHEN u.user_age > 45 THEN o.user_id END) as customers_over_45,
--     sum(oi.quantity * p.external_price) as total_revenue
-- FROM orders o
-- JOIN users u ON o.user_id = u.user_id
-- JOIN order_items oi ON o.order_id = oi.order_id
-- JOIN products p ON oi.product_id = p.product_id
-- WHERE o.order_date >= toStartOfMonth(now()) - INTERVAL 1 MONTH
-- GROUP BY month;

-- -- Sales Metrics
-- CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sales_metrics
-- ENGINE = ReplacingMergeTree(etl_updated_at)
-- ORDER BY (etl_updated_at, month)
-- SETTINGS index_granularity = 8192
-- AS
-- SELECT
--     now() as etl_updated_at,
--     toStartOfMonth(o.order_date) as month,
--     count() as total_orders,
--     sum(oi.quantity) as total_items_sold,
--     count(DISTINCT o.user_id) as unique_customers,
--     sum(oi.quantity * p.external_price) as total_revenue,
--     avg(oi.quantity * p.external_price) as average_order_value,
--     sum(oi.quantity * p.external_price) / count(DISTINCT o.user_id) as revenue_per_customer,
--     sum(oi.quantity) / count() as average_items_per_order
-- FROM orders o
-- JOIN order_items oi ON o.order_id = oi.order_id
-- JOIN products p ON oi.product_id = p.product_id
-- WHERE o.order_date >= toStartOfMonth(now()) - INTERVAL 1 MONTH
-- GROUP BY month;

-- -- Product Performance
-- CREATE MATERIALIZED VIEW IF NOT EXISTS mv_product_performance
-- ENGINE = ReplacingMergeTree(etl_updated_at)
-- ORDER BY (etl_updated_at, month)
-- SETTINGS index_granularity = 8192
-- AS
-- SELECT
--     now() as etl_updated_at,
--     toStartOfMonth(o.order_date) as month,
--     oi.product_id,
--     p.product_name,
--     p.main_category,
--     p.sub_category,
--     count() as total_orders,
--     sum(oi.quantity) as total_quantity_sold,
--     count(DISTINCT o.user_id) as unique_customers,
--     sum(oi.quantity * p.external_price) as total_revenue,
--     avg(oi.quantity * p.external_price) as average_selling_price
-- FROM orders o
-- JOIN order_items oi ON o.order_id = oi.order_id
-- JOIN products p ON oi.product_id = p.product_id
-- WHERE o.order_date >= toStartOfMonth(now()) - INTERVAL 1 MONTH
-- GROUP BY month, oi.product_id, p.product_name, p.main_category, p.sub_category;

