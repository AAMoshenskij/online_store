-- Insert test users
INSERT INTO users (email, password, first_name, last_name, is_verified_email, is_active, role, date_joined)
VALUES 
    ('john.doe@example.com', 'hashed_password', 'John', 'Doe', true, true, 'user', NOW() - INTERVAL '30 days'),
    ('jane.smith@example.com', 'hashed_password', 'Jane', 'Smith', true, true, 'user', NOW() - INTERVAL '25 days'),
    ('bob.wilson@example.com', 'hashed_password', 'Bob', 'Wilson', true, true, 'user', NOW() - INTERVAL '20 days'),
    ('alice.johnson@example.com', 'hashed_password', 'Alice', 'Johnson', true, true, 'seller', NOW() - INTERVAL '15 days'),
    ('charlie.brown@example.com', 'hashed_password', 'Charlie', 'Brown', true, true, 'seller', NOW() - INTERVAL '10 days');

-- Insert test sellers
INSERT INTO sellers (user_id, is_active, created_at)
VALUES 
    (4, true, NOW() - INTERVAL '15 days'),
    (5, true, NOW() - INTERVAL '10 days');

-- Insert test products
INSERT INTO products (product_name, description, status, seller_id, main_category, sub_category, external_price, external_discount_price)
VALUES 
    ('iPhone 13 Pro', 'Latest Apple smartphone', 'published', 1, 'Electronics', 'Smartphones', '999.99', '899.99'),
    ('MacBook Pro', 'Professional laptop', 'published', 1, 'Electronics', 'Laptops', '1299.99', '1199.99'),
    ('Nike Air Max', 'Running shoes', 'published', 2, 'Sports', 'Footwear', '129.99', '99.99'),
    ('Adidas T-Shirt', 'Cotton sports t-shirt', 'published', 2, 'Sports', 'Clothing', '29.99', '24.99'),
    ('Samsung TV', '4K Smart TV', 'published', 1, 'Electronics', 'TVs', '799.99', '699.99');

-- Insert test product variants
INSERT INTO product_variants (product_id, price, stock, option1, option2, option3)
VALUES 
    (1, 999.99, 50, 1, 2, 3),
    (1, 1099.99, 30, 1, 2, 4),
    (2, 1299.99, 20, 5, 6, NULL),
    (2, 1499.99, 15, 5, 7, NULL),
    (3, 129.99, 100, 8, 9, NULL),
    (4, 29.99, 200, 10, 11, NULL),
    (5, 799.99, 25, 12, 13, NULL);

-- Insert test orders for the last 30 days
DO $$
DECLARE
    i INTEGER;
    order_date TIMESTAMP;
    user_id INTEGER;
    product_id INTEGER;
    variant_id INTEGER;
    quantity INTEGER;
    price DECIMAL;
BEGIN
    FOR i IN 1..100 LOOP
        -- Generate random order date within last 30 days
        order_date := NOW() - (random() * INTERVAL '30 days');
        
        -- Select random user (1-3 are regular users)
        user_id := floor(random() * 3) + 1;
        
        -- Create order
        INSERT INTO orders (user_id, status, total_amount, created_at)
        VALUES (user_id, 'completed', 0, order_date)
        RETURNING id INTO order_id;
        
        -- Add 1-3 items to each order
        FOR j IN 1..floor(random() * 3) + 1 LOOP
            -- Select random product and variant
            product_id := floor(random() * 5) + 1;
            variant_id := floor(random() * 7) + 1;
            quantity := floor(random() * 3) + 1;
            
            -- Get price from variant
            SELECT price INTO price FROM product_variants WHERE id = variant_id;
            
            -- Insert order item
            INSERT INTO order_items (order_id, product_id, variant_id, seller_id, quantity, price)
            VALUES (
                order_id,
                product_id,
                variant_id,
                CASE WHEN product_id <= 3 THEN 1 ELSE 2 END,
                quantity,
                price
            );
            
            -- Update order total
            UPDATE orders 
            SET total_amount = total_amount + (price * quantity)
            WHERE id = order_id;
        END LOOP;
        
        -- Add payment
        INSERT INTO payments (order_id, amount, currency, status, payment_method, created_at)
        VALUES (
            order_id,
            (SELECT total_amount FROM orders WHERE id = order_id),
            'USD',
            'completed',
            CASE WHEN random() > 0.5 THEN 'credit_card' ELSE 'paypal' END,
            order_date
        );
    END LOOP;
END $$;

-- Insert some cancelled orders
INSERT INTO orders (user_id, status, total_amount, created_at)
VALUES 
    (1, 'cancelled', 999.99, NOW() - INTERVAL '5 days'),
    (2, 'cancelled', 1299.99, NOW() - INTERVAL '3 days'),
    (3, 'cancelled', 799.99, NOW() - INTERVAL '1 day');

-- Insert some pending orders
INSERT INTO orders (user_id, status, total_amount, created_at)
VALUES 
    (1, 'pending', 129.99, NOW() - INTERVAL '2 hours'),
    (2, 'pending', 29.99, NOW() - INTERVAL '1 hour');

-- Update product ratings
UPDATE products 
SET external_ratings = 4.5 + (random() * 0.5),
    external_ratings_count = floor(random() * 100) + 50
WHERE id IN (1, 2, 3, 4, 5); 