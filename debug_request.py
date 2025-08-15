import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

def debug_request_creation():
    """Отлаживает создание запроса крови"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'Bloodcontrol'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'Vadamahjkl1'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Проверяем структуру таблицы
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'donation_requests'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("Структура таблицы donation_requests:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) as count FROM donation_requests")
        count = cursor.fetchone()['count']
        print(f"\nКоличество записей: {count}")
        
        # Проверяем пользователей-врачей
        cursor.execute("SELECT * FROM users WHERE role = 'doctor'")
        doctors = cursor.fetchall()
        print(f"\nВрачи в системе: {len(doctors)}")
        for doctor in doctors:
            print(f"  {doctor['first_name']} {doctor['last_name']} (ID: {doctor['telegram_id']})")
        
        # Пробуем создать тестовый запрос
        print("\nСоздаем тестовый запрос...")
        test_doctor_id = 123456789
        test_blood_type = 'A+'
        test_location = 'Москва'
        test_date = datetime.now().date()
        
        cursor.execute("""
            INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
            VALUES (%s, %s, %s, %s)
        """, (test_doctor_id, test_blood_type, test_location, test_date))
        
        conn.commit()
        print("✅ Тестовый запрос создан!")
        
        # Проверяем, что запрос создался
        cursor.execute("SELECT * FROM donation_requests WHERE doctor_id = %s", (test_doctor_id,))
        result = cursor.fetchone()
        if result:
            print(f"✅ Запрос найден: ID={result['id']}, группа={result['blood_type']}, место={result['location']}")
        else:
            print("❌ Запрос не найден")
        
        # Удаляем тестовый запрос
        cursor.execute("DELETE FROM donation_requests WHERE doctor_id = %s", (test_doctor_id,))
        conn.commit()
        print("✅ Тестовый запрос удален")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    debug_request_creation() 