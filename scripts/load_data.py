import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import random
from datetime import datetime, timedelta

# Database connection parameters
DB_PARAMS = {
    'dbname': 'online_store',
    'user': 'admin',
    'password': 'admin',
    'host': 'postgres',  # Using localhost since we're running inside the container
    'port': '5432'
}

# Sample sellers data
SELLERS = [
    {
        'username': 'sportsworld',
        'email': 'info@sportsworld.com',
        'password_hash': 'hash1',  # In real app, use proper password hashing
        'company_name': 'Sports World',
        'description': 'Your one-stop shop for all sports equipment'
    },
    {
        'username': 'fitnesspro',
        'email': 'sales@fitnesspro.com',
        'password_hash': 'hash2',
        'company_name': 'Fitness Pro',
        'description': 'Professional fitness equipment and accessories'
    },
    {
        'username': 'outdoorgear',
        'email': 'contact@outdoorgear.com',
        'password_hash': 'hash3',
        'company_name': 'Outdoor Gear',
        'description': 'Quality outdoor and adventure equipment'
    },
    {
        'username': 'dancecentral',
        'email': 'info@dancecentral.com',
        'password_hash': 'hash4',
        'company_name': 'Dance Central',
        'description': 'Everything for dancers and performers'
    },
    {
        'username': 'bagmaster',
        'email': 'sales@bagmaster.com',
        'password_hash': 'hash5',
        'company_name': 'Bag Master',
        'description': 'Premium bags and luggage'
    },
    {
        'username': 'sportselect',
        'email': 'contact@sportselect.com',
        'password_hash': 'hash6',
        'company_name': 'Sport Select',
        'description': 'Specialized sports equipment'
    },
    {
        'username': 'fitnessplus',
        'email': 'info@fitnessplus.com',
        'password_hash': 'hash7',
        'company_name': 'Fitness Plus',
        'description': 'Advanced fitness solutions'
    },
    {
        'username': 'outdoorpro',
        'email': 'sales@outdoorpro.com',
        'password_hash': 'hash8',
        'company_name': 'Outdoor Pro',
        'description': 'Professional outdoor equipment'
    },
    {
        'username': 'danceworld',
        'email': 'contact@danceworld.com',
        'password_hash': 'hash9',
        'company_name': 'Dance World',
        'description': 'World of dance supplies'
    },
    {
        'username': 'bagstore',
        'email': 'info@bagstore.com',
        'password_hash': 'hash10',
        'company_name': 'Bag Store',
        'description': 'Your bag destination'
    }
]

def create_categories(conn):
    """Create main categories and subcategories based on file names"""
    with conn.cursor() as cur:
        # Main categories
        main_categories = [
            'Sports & Fitness',
            'Bags & Luggage',
            'Dance & Performance'
        ]
        
        # Insert main categories
        for category in main_categories:
            cur.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING category_id",
                (category,)
            )
            main_id = cur.fetchone()[0]
            
            # Subcategories based on file names
            if category == 'Sports & Fitness':
                subcategories = ['Exercise and Fitness', 'Sports Fitness and Outdoors', 'Badminton']
            elif category == 'Bags & Luggage':
                subcategories = ['Backpacks', 'Bags and Luggage']
            else:  # Dance & Performance
                subcategories = ['Ballerinas']
            
            # Insert subcategories
            for subcategory in subcategories:
                cur.execute(
                    "INSERT INTO categories (name, parent_id) VALUES (%s, %s)",
                    (subcategory, main_id)
                )
        
        conn.commit()

def load_sellers(conn):
    """Load sellers into the database"""
    with conn.cursor() as cur:
        for seller in SELLERS:
            cur.execute("""
                INSERT INTO sellers (username, email, password_hash, company_name, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING seller_id
            """, (
                seller['username'],
                seller['email'],
                seller['password_hash'],
                seller['company_name'],
                seller['description']
            ))
        conn.commit()

def process_product_data(conn, file_path):
    """Process a single product data file"""
    # Read CSV file
    df = pd.read_csv(file_path)
    
    # Get category IDs
    with conn.cursor() as cur:
        # Get main category ID
        main_category = os.path.basename(file_path).split('.')[0]
        cur.execute("SELECT category_id FROM categories WHERE name = %s", (main_category,))
        main_category_id = cur.fetchone()[0]
        
        # Get subcategory ID
        subcategory = os.path.basename(file_path).split('.')[0]
        cur.execute("SELECT category_id FROM categories WHERE name = %s", (subcategory,))
        subcategory_id = cur.fetchone()[0]
    
    # Prepare product data
    products = []
    for _, row in df.iterrows():
        # Randomly assign a seller
        seller_id = random.randint(1, len(SELLERS))
        
        # Convert price strings to decimal
        try:
            price = float(str(row['actual_price']).replace('₹', '').replace(',', ''))
            discount_price = float(str(row['discount_price']).replace('₹', '').replace(',', ''))
        except (ValueError, AttributeError):
            price = 0.0
            discount_price = 0.0
        
        # Create random creation date within last year
        created_at = datetime.now() - timedelta(days=random.randint(0, 365))
        
        products.append((
            seller_id,
            row['name'],
            row.get('description', ''),  # Some files might not have description
            main_category_id,
            subcategory_id,
            price,
            discount_price,
            row['image'],
            row['link'],
            created_at,
            created_at  # updated_at same as created_at initially
        ))
    
    # Insert products in batches
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO products (
                seller_id, name, description, main_category_id, sub_category_id,
                price, discount_price, image_url, product_url, created_at, updated_at
            ) VALUES %s
        """, products)
    
    conn.commit()

def main():
    # Connect to PostgreSQL
    conn = psycopg2.connect(**DB_PARAMS)
    
    try:
        # Create categories
        create_categories(conn)
        
        # Load sellers
        load_sellers(conn)
        
        # Process all CSV files in the data directory
        data_dir = '/data'  # Updated path for container
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(data_dir, filename)
                print(f"Processing {filename}...")
                process_product_data(conn, file_path)
                print(f"Completed processing {filename}")
        
        print("Data loading completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 