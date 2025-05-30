-- -- Create airflow user and database
-- CREATE USER airflow WITH PASSWORD 'airflow';
-- CREATE DATABASE airflow;
-- GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- -- Create online store database
-- -- CREATE DATABASE online_store;
-- -- \c online_store;

-- -- Create users table
-- CREATE TABLE IF NOT EXISTS users (
--     user_id SERIAL PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     email VARCHAR(100) UNIQUE NOT NULL,
--     password_hash VARCHAR(255) NOT NULL,
--     first_name VARCHAR(50),
--     last_name VARCHAR(50),
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- Create sellers table
-- CREATE TABLE IF NOT EXISTS sellers (
--     seller_id SERIAL PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     email VARCHAR(100) UNIQUE NOT NULL,
--     password_hash VARCHAR(255) NOT NULL,
--     company_name VARCHAR(100),
--     description TEXT,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- Create categories table
-- CREATE TABLE IF NOT EXISTS categories (
--     category_id SERIAL PRIMARY KEY,
--     name VARCHAR(100) NOT NULL,
--     parent_id INTEGER REFERENCES categories(category_id),
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- Create products table
-- CREATE TABLE IF NOT EXISTS products (
--     product_id SERIAL PRIMARY KEY,
--     seller_id INTEGER REFERENCES sellers(seller_id),
--     name VARCHAR(255) NOT NULL,
--     description TEXT,
--     main_category_id INTEGER REFERENCES categories(category_id),
--     sub_category_id INTEGER REFERENCES categories(category_id),
--     price DECIMAL(10,2) NOT NULL,
--     discount_price DECIMAL(10,2),
--     image_url VARCHAR(255),
--     product_url VARCHAR(255),
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- Create product_ratings table
-- CREATE TABLE IF NOT EXISTS  product_ratings (
--     rating_id SERIAL PRIMARY KEY,
--     product_id INTEGER REFERENCES products(product_id),
--     user_id INTEGER REFERENCES users(user_id),
--     rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5),
--     review TEXT,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- Create indexes
-- CREATE INDEX idx_products_seller ON products(seller_id);
-- CREATE INDEX idx_products_categories ON products(main_category_id, sub_category_id);
-- CREATE INDEX idx_ratings_product ON product_ratings(product_id);
-- CREATE INDEX idx_ratings_user ON product_ratings(user_id);

-- -- Create function to update updated_at timestamp
-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = CURRENT_TIMESTAMP;
--     RETURN NEW;
-- END;
-- $$ language 'plpgsql';

-- -- Create triggers for updated_at
-- CREATE TRIGGER update_users_updated_at
--     BEFORE UPDATE ON users
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- CREATE TRIGGER update_sellers_updated_at
--     BEFORE UPDATE ON sellers
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- CREATE TRIGGER update_products_updated_at
--     BEFORE UPDATE ON products
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- CREATE TRIGGER update_ratings_updated_at
--     BEFORE UPDATE ON product_ratings
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column(); 