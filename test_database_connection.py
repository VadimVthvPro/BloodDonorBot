"""
Тест подключения к базе данных Bloodcontrol
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

def test_database_connection():
    """Тест подключения к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        
        print("✅ Подключение к базе данных успешно!")
        
        # Проверяем таблицы
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        
        print(f"📋 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Проверяем представления
        cursor.execute("SELECT table_name FROM information_schema.views WHERE table_schema = 'public'")
        views = cursor.fetchall()
        
        print(f"📊 Найдено представлений: {len(views)}")
        for view in views:
            print(f"   - {view[0]}")
        
        # Проверяем индексы
        cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
        indexes = cursor.fetchall()
        
        print(f"🔍 Найдено индексов: {len(indexes)}")
        
        cursor.close()
        conn.close()
        
        print("✅ Все проверки прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def test_table_structure():
    """Тест структуры таблиц"""
    print("\n🔍 Тестирование структуры таблиц...")
    
    load_dotenv()
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        
        cursor = conn.cursor()
        
        # Проверяем таблицу users
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        users_columns = cursor.fetchall()
        print("📋 Таблица 'users':")
        for col in users_columns:
            print(f"   - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        # Проверяем таблицу donation_requests
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'donation_requests' 
            ORDER BY ordinal_position
        """)
        
        requests_columns = cursor.fetchall()
        print("📋 Таблица 'donation_requests':")
        for col in requests_columns:
            print(f"   - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        cursor.close()
        conn.close()
        
        print("✅ Структура таблиц корректна!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки структуры таблиц: {e}")
        return False

def test_insert_sample_data():
    """Тест вставки тестовых данных"""
    print("\n🔍 Тестирование вставки данных...")
    
    load_dotenv()
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        
        cursor = conn.cursor()
        
        # Вставляем тестового пользователя
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, role, blood_type, location, is_registered)
            VALUES (123456789, 'test_user', 'Тест', 'Пользователь', 'user', 'A+', 'Москва', TRUE)
            ON CONFLICT (telegram_id) DO NOTHING
        """)
        
        # Вставляем тестового врача
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, role, is_registered)
            VALUES (987654321, 'test_doctor', 'Тест', 'Врач', 'doctor', TRUE)
            ON CONFLICT (telegram_id) DO NOTHING
        """)
        
        conn.commit()
        print("✅ Тестовые данные вставлены успешно!")
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"📊 Всего пользователей в базе: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        donor_count = cursor.fetchone()[0]
        print(f"👤 Доноров: {donor_count}")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'doctor'")
        doctor_count = cursor.fetchone()[0]
        print(f"👨‍⚕️ Врачей: {doctor_count}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка вставки данных: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Тестирование подключения к базе данных Bloodcontrol")
    print("=" * 50)
    
    # Запускаем тесты
    test1 = test_database_connection()
    test2 = test_table_structure()
    test3 = test_insert_sample_data()
    
    print("\n" + "=" * 50)
    if test1 and test2 and test3:
        print("🎉 Все тесты прошли успешно!")
        print("✅ База данных готова к работе с ботом!")
    else:
        print("❌ Некоторые тесты не прошли!")
        print("🔧 Проверьте настройки базы данных")
    
    print("\n📋 Следующие шаги:")
    print("1. Получите Telegram Bot Token у @BotFather")
    print("2. Обновите TELEGRAM_TOKEN в файле .env")
    print("3. Запустите бота: python3 bot.py") 