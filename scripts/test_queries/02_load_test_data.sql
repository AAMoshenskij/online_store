-- Generate test users
INSERT INTO users (age, email, password, first_name, last_name, is_verified_email, is_active, role, date_joined, last_login)
VALUES 
    (25, 'john.doe@example.com', crypt('password123', gen_salt('bf')), 'John', 'Doe', true, true, 'user', NOW() - INTERVAL '30 days', NOW() - INTERVAL '1 day'),
    (30, 'jane.smith@example.com', crypt('password123', gen_salt('bf')), 'Jane', 'Smith', true, true, 'user', NOW() - INTERVAL '25 days', NOW() - INTERVAL '2 days'),
    (35, 'bob.johnson@example.com', crypt('password123', gen_salt('bf')), 'Bob', 'Johnson', false, true, 'user', NOW() - INTERVAL '20 days', NOW() - INTERVAL '3 days'),
    (28, 'alice.brown@example.com', crypt('password123', gen_salt('bf')), 'Alice', 'Brown', true, false, 'user', NOW() - INTERVAL '15 days', NOW() - INTERVAL '4 days'),
    (40, 'charlie.wilson@example.com', crypt('password123', gen_salt('bf')), 'Charlie', 'Wilson', true, true, 'user', NOW() - INTERVAL '10 days', NOW() - INTERVAL '5 days');

-- Generate test sellers
INSERT INTO sellers (first_name, last_name, user_id, is_active, created_at)
SELECT 
    first_name,
    last_name,
    id,
    true,
    date_joined
FROM users
LIMIT 2 OFFSET 2; 

-- Generate test products
INSERT INTO products (
    product_name, 
    description,
    status,
    seller_id,
    main_category,
    sub_category,
    external_ratings,
    external_ratings_count,
    external_price,
    created_at
)
SELECT 
    p.name,
    p.description,
    'published',
    s.id,
    p.category,
    p.subcategory,
    p.rating,
    p.rating_count,
    p.price,
    NOW() - (RANDOM() * INTERVAL '30 days')
FROM (
    VALUES 
        ('iPhone 13', 'Latest iPhone model', 'Electronics', 'Phones', 4.5, 1000, '999.99'),
        ('MacBook Pro', 'Powerful laptop for professionals', 'Electronics', 'Laptops', 4.8, 800, '1299.99'),
        ('Nike Air Max', 'Comfortable running shoes', 'Sports', 'Fitness', 4.3, 500, '129.99'),
        ('Python Programming', 'Learn Python programming', 'Books', 'Educational', 4.7, 300, '49.99'),
        ('Coffee Maker', 'Automatic coffee machine', 'Home', 'Kitchen', 4.2, 200, '79.99'),
        ('Gaming Mouse', 'High-precision gaming mouse', 'Electronics', 'Accessories', 4.4, 400, '59.99'),
        ('Yoga Mat', 'Non-slip yoga mat', 'Sports', 'Fitness', 4.1, 150, '29.99'),
        ('Novel: The Journey', 'Bestselling fiction novel', 'Books', 'Fiction', 4.6, 250, '19.99'),
        ('Smart Watch', 'Feature-rich smartwatch', 'Electronics', 'Accessories', 4.3, 350, '199.99'),
        ('Blender', 'High-speed blender', 'Home', 'Kitchen', 4.0, 180, '89.99')
) AS p(name, description, category, subcategory, rating, rating_count, price)
CROSS JOIN sellers s
ORDER BY RANDOM()
LIMIT 100;

-- Generate test orders and related data
DO $$
DECLARE
    user_id INT;
    product_id INT;
    seller_id INT;
    order_id INT;
    order_total DECIMAL(10,2);
BEGIN
    -- Create orders for each user
    FOR user_id IN SELECT id FROM users LOOP
        -- Create 2-3 orders per user
        FOR i IN 1..FLOOR(RANDOM() * 2 + 2) LOOP
            -- Create order
            INSERT INTO orders (user_id, status, total_amount, created_at)
            VALUES (user_id, 
                   CASE FLOOR(RANDOM() * 3)::INT
                       WHEN 0 THEN 'pending'
                       WHEN 1 THEN 'completed'
                       ELSE 'cancelled'
                   END,
                   0, -- Will be updated after adding items
                   NOW() - (RANDOM() * INTERVAL '30 days'))
            RETURNING id INTO order_id;

            DECLARE
                order_total DECIMAL(10,2) := 0;
            BEGIN
                -- Add 1-3 items to each order
                FOR j IN 1..FLOOR(RANDOM() * 3 + 1) LOOP
                    -- Get random product and seller
                    SELECT p.id, p.seller_id INTO product_id, seller_id 
                    FROM products p
                    ORDER BY RANDOM() 
                    LIMIT 1;

                    -- Calculate item price
                    DECLARE
                        item_price DECIMAL(10,2);
                        item_quantity INT;
                    BEGIN
                        item_quantity := FLOOR(RANDOM() * 5 + 1)::INT;
                        item_price := (SELECT external_price::DECIMAL * item_quantity FROM products WHERE id = product_id);
                        order_total := order_total + item_price;

                        -- Add order item
                        INSERT INTO order_items (order_id, product_id, seller_id, quantity, price)
                        VALUES (order_id, product_id, seller_id, item_quantity, item_price);

                        -- Create payment
                        INSERT INTO payments (order_id, amount, currency, status, payment_method, created_at)
                        VALUES (
                            order_id,
                            item_price,
                            'USD',
                            CASE FLOOR(RANDOM() * 3)::INT
                                WHEN 0 THEN 'pending'
                                WHEN 1 THEN 'completed'
                                ELSE 'failed'
                            END,
                            CASE FLOOR(RANDOM() * 3)::INT
                                WHEN 0 THEN 'credit_card'
                                WHEN 1 THEN 'paypal'
                                ELSE 'bank_transfer'
                            END,
                            NOW() - (RANDOM() * INTERVAL '30 days')
                        );
                    END;
                END LOOP;

                -- Update order total amount
                UPDATE orders SET total_amount = order_total WHERE id = order_id;
            END;
        END LOOP;
    END LOOP;
END $$; 