import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Настройка подключения к базе данных
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_users(session):
    users_data = [
        {
            "email": "admin@example.com",
            "password": pwd_context.hash("admin123"),
            "first_name": "Admin",
            "last_name": "User",
            "is_verified_email": True,
            "is_active": True,
            "is_superuser": True,
            "role": "admin"
        },
        {
            "email": "seller1@example.com",
            "password": pwd_context.hash("seller123"),
            "first_name": "John",
            "last_name": "Doe",
            "is_verified_email": True,
            "is_active": True,
            "is_superuser": False,
            "role": "seller"
        },
        {
            "email": "seller2@example.com",
            "password": pwd_context.hash("seller123"),
            "first_name": "Jane",
            "last_name": "Smith",
            "is_verified_email": True,
            "is_active": True,
            "is_superuser": False,
            "role": "seller"
        },
        {
            "email": "user1@example.com",
            "password": pwd_context.hash("user123"),
            "first_name": "Alice",
            "last_name": "Johnson",
            "is_verified_email": True,
            "is_active": True,
            "is_superuser": False,
            "role": "user"
        },
        {
            "email": "user2@example.com",
            "password": pwd_context.hash("user123"),
            "first_name": "Bob",
            "last_name": "Brown",
            "is_verified_email": True,
            "is_active": True,
            "is_superuser": False,
            "role": "user"
        }
    ]
    
    user_ids = []
    for user_data in users_data:
        result = session.execute(
            text("""
                INSERT INTO users (email, password, first_name, last_name, is_verified_email, 
                                 is_active, is_superuser, role, date_joined)
                VALUES (:email, :password, :first_name, :last_name, :is_verified_email,
                        :is_active, :is_superuser, :role, :date_joined)
                RETURNING id
            """),
            {**user_data, "date_joined": datetime.now()}
        )
        user_ids.append(result.scalar())
    
    return user_ids

def create_sellers(session, user_ids):
    sellers_data = [
        {"user_id": user_ids[1], "first_name": "John", "last_name": "Doe"},
        {"user_id": user_ids[2], "first_name": "Jane", "last_name": "Smith"}
    ]
    
    seller_ids = []
    for seller_data in sellers_data:
        result = session.execute(
            text("""
                INSERT INTO sellers (user_id, first_name, last_name, created_at)
                VALUES (:user_id, :first_name, :last_name, :created_at)
                RETURNING id
            """),
            {**seller_data, "created_at": datetime.now()}
        )
        seller_ids.append(result.scalar())
    
    return seller_ids

def create_product_variants(session, product_id, base_price):
    # Создаем опции для продукта
    options_data = [
        {"name": "Size", "items": ["S", "M", "L", "XL"]},
        {"name": "Color", "items": ["Red", "Blue", "Black", "White"]}
    ]
    
    option_ids = []
    option_item_ids = {}
    
    for option_data in options_data:
        # Создаем опцию
        result = session.execute(
            text("""
                INSERT INTO product_options (product_id, option_name)
                VALUES (:product_id, :option_name)
                RETURNING id
            """),
            {
                "product_id": product_id,
                "option_name": option_data["name"]
            }
        )
        option_id = result.scalar()
        option_ids.append(option_id)
        
        # Создаем значения опции
        option_item_ids[option_id] = []
        for item_name in option_data["items"]:
            result = session.execute(
                text("""
                    INSERT INTO product_option_items (option_id, item_name)
                    VALUES (:option_id, :item_name)
                    RETURNING id
                """),
                {
                    "option_id": option_id,
                    "item_name": item_name
                }
            )
            option_item_ids[option_id].append(result.scalar())
    
    # Создаем варианты продукта
    for size_id in option_item_ids[option_ids[0]]:  # Size
        for color_id in option_item_ids[option_ids[1]]:  # Color
            # Используем базовую цену из CSV с небольшими вариациями для разных размеров
            price = base_price * (1 + (size_id * 0))  # Увеличиваем цену на 10% для каждого размера
            stock = (size_id + color_id) * 10
            
            session.execute(
                text("""
                    INSERT INTO product_variants (
                        product_id, price, stock, option1, option2,
                        created_at, updated_at
                    )
                    VALUES (
                        :product_id, :price, :stock, :option1, :option2,
                        :created_at, :updated_at
                    )
                """),
                {
                    "product_id": product_id,
                    "price": price,
                    "stock": stock,
                    "option1": size_id,
                    "option2": color_id,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            )

def create_products(session, seller_ids):
    # Читаем CSV файлы из директории data
    data_dir = "data"
    product_ids = []
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            df = pd.read_csv(os.path.join(data_dir, filename))
            
            for _, row in df.iterrows():
                # Обработка числовых значений
                def clean_number(value):
                    if pd.isna(value):
                        return None
                    if isinstance(value, str):
                        # Удаляем все символы кроме цифр, точки, запятой и пробела
                        value = ''.join(c for c in value if c.isdigit() or c in '., ')
                        # Удаляем пробелы (разделители тысяч)
                        value = value.replace(' ', '')
                        # Заменяем запятую на точку для корректного преобразования в float
                        value = value.replace(',', '.')
                        # Если после очистки строка пустая, возвращаем None
                        if not value:
                            return None
                        try:
                            # Пробуем преобразовать в float
                            return str(float(value))
                        except ValueError:
                            return None
                    return str(value) if value else None

                # Создаем продукт
                result = session.execute(
                    text("""
                        INSERT INTO products (
                            product_name, description, status, main_category, sub_category,
                            external_image_url, external_link, external_ratings,
                            external_ratings_count, external_discount_price, external_price,
                            created_at, published_at, seller_id
                        )
                        VALUES (
                            :name, :description, :status, :main_category, :sub_category,
                            :image, :link, :ratings, :no_of_ratings, :discount_price,
                            :actual_price, :created_at, :published_at, :seller_id
                        )
                        RETURNING id
                    """),
                    {
                        "name": row['name'],
                        "description": f"Description for {row['name']}",
                        "status": "published",
                        "main_category": row['main_category'],
                        "sub_category": row['sub_category'],
                        "image": row['image'],
                        "link": row['link'],
                        "ratings": clean_number(row['ratings']),
                        "no_of_ratings": int(float(clean_number(row['no_of_ratings']) or 0)),
                        "discount_price": clean_number(row['discount_price']),
                        "actual_price": clean_number(row['actual_price']),
                        "created_at": datetime.now(),
                        "published_at": datetime.now(),
                        "seller_id": seller_ids[0] if len(product_ids) % 2 == 0 else seller_ids[1]
                    }
                )
                product_id = result.scalar()
                product_ids.append(product_id)
                
                # Создаем медиа для продукта
                session.execute(
                    text("""
                        INSERT INTO product_media (product_id, alt, src, type, created_at)
                        VALUES (:product_id, :alt, :src, :type, :created_at)
                    """),
                    {
                        "product_id": product_id,
                        "alt": row['name'],
                        "src": row['image'],
                        "type": "image",
                        "created_at": datetime.now()
                    }
                )
                
                # Создаем варианты продукта
                create_product_variants(session, product_id, float(clean_number(row['actual_price']) or 0))
    
    return product_ids

def main():
    try:
        session = SessionLocal()
        
        # Проверяем наличие данных
        result = session.execute(text("SELECT COUNT(*) FROM products"))
        products_count = result.scalar()
        
        if products_count > 0:
            print("Database already contains data, skipping seeding")
            return
        
        # Создаем пользователей
        print("Creating users...")
        user_ids = create_users(session)
        
        # Создаем продавцов
        print("Creating sellers...")
        seller_ids = create_sellers(session, user_ids)
        
        # Создаем продукты
        print("Creating products...")
        product_ids = create_products(session, seller_ids)
        
        # Обновляем product_ids у продавцов
        for seller_id in seller_ids:
            session.execute(
                text("""
                    UPDATE sellers 
                    SET product_ids = (
                        SELECT array_agg(id) 
                        FROM products 
                        WHERE seller_id = :seller_id
                    )
                    WHERE id = :seller_id
                """),
                {"seller_id": seller_id}
            )
        
        session.commit()
        print("Data seeding completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main() 