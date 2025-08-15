import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_requests():
    """Проверяет запросы в базе данных"""
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
        
        # Проверяем все запросы
        cursor.execute("""
            SELECT dr.*, u.first_name, u.last_name
            FROM donation_requests dr
            LEFT JOIN users u ON dr.doctor_id = u.telegram_id
            ORDER BY dr.created_at DESC
        """)
        
        requests = cursor.fetchall()
        
        print(f"Найдено запросов: {len(requests)}")
        
        for req in requests:
            print(f"\nЗапрос #{req['id']}:")
            print(f"  Врач: {req['first_name']} {req['last_name']} (ID: {req['doctor_id']})")
            print(f"  Группа крови: {req['blood_type']}")
            print(f"  Местоположение: {req['location']}")
            print(f"  Дата запроса: {req['request_date']}")
            print(f"  Создан: {req['created_at']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    check_requests() 