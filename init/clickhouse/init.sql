-- Create database
CREATE DATABASE IF NOT EXISTS online_store;

USE online_store;

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id UInt32,
    seller_id UInt32,
    name String,
    description String,
    main_category_id UInt32,
    sub_category_id UInt32,
    price Decimal(10,2),
    discount_price Decimal(10,2),
    image_url String,
    product_url String,
    created_at DateTime,
    updated_at DateTime
) ENGINE = MergeTree()
ORDER BY (product_id, seller_id);

-- Create product_ratings table
CREATE TABLE IF NOT EXISTS product_ratings (
    rating_id UInt32,
    product_id UInt32,
    user_id UInt32,
    rating Decimal(2,1),
    review String,
    created_at DateTime,
    updated_at DateTime
) ENGINE = MergeTree()
ORDER BY (product_id, user_id);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    event_id UUID,
    event_type Enum('purchase' = 1, 'order_received' = 2, 'order_cancelled' = 3, 'rating_added' = 4, 'rating_updated' = 5),
    user_id UInt32,
    product_id UInt32,
    quantity UInt32,
    price Decimal(10,2),
    rating Decimal(2,1),
    review String,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY (timestamp, event_type, user_id, product_id);

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS product_analytics
ENGINE = SummingMergeTree()
ORDER BY (product_id, date)
AS
SELECT
    product_id,
    toDate(timestamp) as date,
    count() as total_events,
    sum(if(event_type = 'purchase', quantity, 0)) as total_purchases,
    sum(if(event_type = 'purchase', quantity * price, 0)) as total_revenue,
    avg(if(event_type IN ('rating_added', 'rating_updated'), rating, null)) as avg_rating
FROM events
GROUP BY product_id, date;

CREATE MATERIALIZED VIEW IF NOT EXISTS seller_analytics
ENGINE = SummingMergeTree()
ORDER BY (seller_id, date)
AS
SELECT
    p.seller_id,
    toDate(e.timestamp) as date,
    count() as total_events,
    sum(if(e.event_type = 'purchase', e.quantity, 0)) as total_purchases,
    sum(if(e.event_type = 'purchase', e.quantity * e.price, 0)) as total_revenue,
    avg(if(e.event_type IN ('rating_added', 'rating_updated'), e.rating, null)) as avg_rating
FROM events e
JOIN products p ON e.product_id = p.product_id
GROUP BY p.seller_id, date;

CREATE MATERIALIZED VIEW IF NOT EXISTS category_analytics
ENGINE = SummingMergeTree()
ORDER BY (category_id, date)
AS
SELECT
    p.main_category_id as category_id,
    toDate(e.timestamp) as date,
    count() as total_events,
    sum(if(e.event_type = 'purchase', e.quantity, 0)) as total_purchases,
    sum(if(e.event_type = 'purchase', e.quantity * e.price, 0)) as total_revenue,
    avg(if(e.event_type IN ('rating_added', 'rating_updated'), e.rating, null)) as avg_rating
FROM events e
JOIN products p ON e.product_id = p.product_id
GROUP BY p.main_category_id, date; 