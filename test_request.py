import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

def test_create_request():
    """Тестирует создание запроса крови"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'Bloodcontrol'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'Vadamahjkl1'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Создаем тестовый запрос
        doctor_id = 123456789
        blood_type = 'A+'
        location = 'Москва'
        request_date = datetime.now().date()
        
        print(f"Создаем запрос:")
        print(f"  Врач ID: {doctor_id}")
        print(f"  Группа крови: {blood_type}")
        print(f"  Местоположение: {location}")
        print(f"  Дата: {request_date}")
        
        cursor.execute("""
            INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
            VALUES (%s, %s, %s, %s)
        """, (doctor_id, blood_type, location, request_date))
        
        conn.commit()
        print("✅ Запрос успешно создан!")
        
        # Проверяем, что запрос создался
        cursor.execute("SELECT * FROM donation_requests WHERE doctor_id = %s", (doctor_id,))
        result = cursor.fetchone()
        if result:
            print(f"✅ Запрос найден в БД: {result}")
        else:
            print("❌ Запрос не найден в БД")
        
        # Удаляем тестовый запрос
        cursor.execute("DELETE FROM donation_requests WHERE doctor_id = %s", (doctor_id,))
        conn.commit()
        print("✅ Тестовый запрос удален")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_create_request() 