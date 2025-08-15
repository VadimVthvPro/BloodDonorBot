import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_donation_requests_table():
    """Проверяет структуру таблицы donation_requests"""
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
            SELECT column_name, data_type, is_nullable, column_default
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
        print(f"\nКоличество записей в таблице: {count}")
        
        # Пробуем вставить тестовую запись
        print("\nПробуем вставить тестовую запись...")
        cursor.execute("""
            INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
            VALUES (%s, %s, %s, %s)
        """, (123456789, 'A+', 'Москва', '2024-12-25'))
        
        conn.commit()
        print("✅ Тестовая запись успешно добавлена!")
        
        # Проверяем количество записей после вставки
        cursor.execute("SELECT COUNT(*) as count FROM donation_requests")
        count = cursor.fetchone()['count']
        print(f"Количество записей после вставки: {count}")
        
        # Удаляем тестовую запись
        cursor.execute("DELETE FROM donation_requests WHERE doctor_id = 123456789")
        conn.commit()
        print("✅ Тестовая запись удалена")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    check_donation_requests_table() 