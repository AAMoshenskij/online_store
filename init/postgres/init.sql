ALTER SYSTEM SET wal_level = 'logical';
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    -- age INTEGER DEFAULT randUniform(18, 55),
    age INTEGER DEFAULT 21,
    email VARCHAR(256) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    first_name VARCHAR(256),
    last_name VARCHAR(256),
    is_verified_email BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    role VARCHAR(6) DEFAULT 'user',
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create users_verifications table
CREATE TABLE users_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    request_type VARCHAR,
    new_email VARCHAR(256),
    new_phone VARCHAR(256),
    active_access_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create sellers table
CREATE TABLE sellers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(256),
    last_name VARCHAR(256),
    user_id INTEGER UNIQUE REFERENCES users(id),
    product_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_activities table
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT 'empty',
    status TEXT DEFAULT 'draft',
    main_category VARCHAR(100),
    sub_category VARCHAR(200),
    external_image_url VARCHAR(500),
    external_link VARCHAR(500),
    external_ratings FLOAT,
    external_ratings_count INTEGER,
    external_discount_price VARCHAR(50),
    external_price VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    seller_id INTEGER NOT NULL REFERENCES sellers(id)
);

-- Create product_options table
CREATE TABLE product_options (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    option_name VARCHAR(255) NOT NULL,
    UNIQUE (product_id, option_name)
);

-- Create product_option_items table
CREATE TABLE product_option_items (
    id SERIAL PRIMARY KEY,
    option_id INTEGER NOT NULL REFERENCES product_options(id),
    item_name VARCHAR(255) NOT NULL,
    UNIQUE (option_id, item_name)
);

-- Create product_variants table
CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    price NUMERIC(12, 2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    option1 INTEGER REFERENCES product_option_items(id) ON DELETE SET NULL,
    option2 INTEGER REFERENCES product_option_items(id) ON DELETE SET NULL,
    option3 INTEGER REFERENCES product_option_items(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create product_media table
CREATE TABLE product_media (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    alt VARCHAR,
    src TEXT NOT NULL,
    type VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'created',
    total_amount NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create order_items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    variant_id INTEGER REFERENCES product_variants(id) ON DELETE SET NULL,
    seller_id INTEGER NOT NULL REFERENCES sellers(id),
    quantity INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

-- Create payments table
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_intent_id VARCHAR(100),
    payment_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);


