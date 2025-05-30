import psycopg2
import random
from datetime import datetime, timedelta
from faker import Faker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'dbname': 'online_store',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'postgres',
    'port': '5432'
}

# Initialize Faker
fake = Faker()

def create_connection():
    """Create a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def generate_users(conn, count=10):
    """Generate test users."""
    cursor = conn.cursor()
    try:
        for _ in range(count):
            cursor.execute("""
                INSERT INTO users (age, first_name, last_name, is_verified_email, is_active, date_joined, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                random.randint(18, 65),
                fake.first_name(),
                fake.last_name(),
                random.choice([True, False]),
                random.choice([True, False]),
                fake.date_time_this_year(),
                fake.date_time_this_month()
            ))
        conn.commit()
        logger.info(f"Generated {count} users")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error generating users: {e}")
        raise

def generate_sellers(conn, count=5):
    """Generate test sellers."""
    cursor = conn.cursor()
    try:
        for _ in range(count):
            cursor.execute("""
                INSERT INTO sellers (first_name, last_name)
                VALUES (%s, %s)
                RETURNING id
            """, (
                fake.first_name(),
                fake.last_name()
            ))
        conn.commit()
        logger.info(f"Generated {count} sellers")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error generating sellers: {e}")
        raise

def generate_products(conn, count=20):
    """Generate test products."""
    cursor = conn.cursor()
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
    subcategories = {
        'Electronics': ['Phones', 'Laptops', 'Accessories'],
        'Clothing': ['Men', 'Women', 'Kids'],
        'Books': ['Fiction', 'Non-Fiction', 'Educational'],
        'Home': ['Furniture', 'Decor', 'Kitchen'],
        'Sports': ['Fitness', 'Outdoor', 'Team Sports']
    }
    
    try:
        for _ in range(count):
            main_category = random.choice(categories)
            sub_category = random.choice(subcategories[main_category])
            cursor.execute("""
                INSERT INTO products (product_name, main_category, sub_category, external_ratings, external_ratings_count, external_price)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                fake.catch_phrase(),
                main_category,
                sub_category,
                round(random.uniform(1, 5), 1),
                random.randint(0, 1000),
                str(round(random.uniform(10, 1000), 2))
            ))
        conn.commit()
        logger.info(f"Generated {count} products")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error generating products: {e}")
        raise

def generate_orders(conn, count=50):
    """Generate test orders with items and payments."""
    cursor = conn.cursor()
    try:
        # Get all user IDs
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Get all product IDs
        cursor.execute("SELECT id FROM products")
        product_ids = [row[0] for row in cursor.fetchall()]
        
        # Get all seller IDs
        cursor.execute("SELECT id FROM sellers")
        seller_ids = [row[0] for row in cursor.fetchall()]
        
        for _ in range(count):
            # Create order
            order_date = fake.date_time_this_month()
            cursor.execute("""
                INSERT INTO orders (user_id, status, created_at)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                random.choice(user_ids),
                random.choice(['pending', 'completed', 'cancelled']),
                order_date
            ))
            order_id = cursor.fetchone()[0]
            
            # Create order items (1-3 items per order)
            num_items = random.randint(1, 3)
            for _ in range(num_items):
                product_id = random.choice(product_ids)
                seller_id = random.choice(seller_ids)
                quantity = random.randint(1, 5)
                
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, seller_id, quantity)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, product_id, seller_id, quantity))
            
            # Create payment
            cursor.execute("""
                INSERT INTO payments (order_id, amount, currency, status, payment_method, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                round(random.uniform(10, 1000), 2),
                'USD',
                random.choice(['pending', 'completed', 'failed']),
                random.choice(['credit_card', 'paypal', 'bank_transfer']),
                order_date + timedelta(minutes=random.randint(1, 30))
            ))
            
        conn.commit()
        logger.info(f"Generated {count} orders with items and payments")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error generating orders: {e}")
        raise

def main():
    """Main function to generate all test data."""
    conn = create_connection()
    try:
        # Generate data in correct order
        generate_users(conn)
        generate_sellers(conn)
        generate_products(conn)
        generate_orders(conn)
        logger.info("Test data generation completed successfully")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
 