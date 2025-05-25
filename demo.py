from apps.accounts.models import User
from apps.accounts.services.password import PasswordManager
from config.database import DatabaseManager

# 1. Создаем сессию
session = DatabaseManager.session

try:
    # 2. Находим пользователя
    user = session.query(User).filter(User.email == "admin@example.com").first()
    
    if not user:
        print("Пользователь не найден")
    else:
        # 3. Хешируем новый пароль
        new_password = "AdminPassword123"  # Замените на реальный пароль
        hashed_password = PasswordManager.hash_password(new_password)
        
        # 4. Обновляем пароль
        user.password = hashed_password
        session.commit()
        print(f"Пароль для {user.email} успешно изменён")
finally:
    session.close()

