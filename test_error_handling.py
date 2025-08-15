import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

def test_error_handling():
    """Тестирует обработку ошибок"""
    
    # Тестируем подключение к базе данных
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
        
        print("✅ Подключение к базе данных успешно")
        
        # Тестируем обработку ошибок при вставке
        print("\nТестируем обработку ошибок при вставке данных:")
        
        # Попытка вставить запрос с несуществующим врачом
        try:
            cursor.execute("""
                INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
                VALUES (%s, %s, %s, %s)
            """, (999999999, 'A+', 'Москва', datetime.now().date()))
            conn.commit()
            print("  Вставка с несуществующим врачом -> Успешно (но может быть ошибка FK)")
        except Exception as e:
            print(f"  Вставка с несуществующим врачом -> Ошибка: {e}")
        
        # Попытка вставить запрос с неверной группой крови
        try:
            cursor.execute("""
                INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
                VALUES (%s, %s, %s, %s)
            """, (123456789, 'INVALID', 'Москва', datetime.now().date()))
            conn.commit()
            print("  Вставка с неверной группой крови -> Успешно (нет ограничений)")
        except Exception as e:
            print(f"  Вставка с неверной группой крови -> Ошибка: {e}")
        
        # Попытка вставить запрос с пустым местоположением
        try:
            cursor.execute("""
                INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
                VALUES (%s, %s, %s, %s)
            """, (123456789, 'A+', '', datetime.now().date()))
            conn.commit()
            print("  Вставка с пустым местоположением -> Успешно (пустая строка разрешена)")
        except Exception as e:
            print(f"  Вставка с пустым местоположением -> Ошибка: {e}")
        
        # Попытка вставить запрос с неверной датой
        try:
            cursor.execute("""
                INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
                VALUES (%s, %s, %s, %s)
            """, (123456789, 'A+', 'Москва', 'invalid_date'))
            conn.commit()
            print("  Вставка с неверной датой -> Успешно (ошибка будет в Python)")
        except Exception as e:
            print(f"  Вставка с неверной датой -> Ошибка: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
    
    # Тестируем обработку ошибок в Python
    print("\nТестируем обработку ошибок в Python:")
    
    # Обработка неверной даты
    try:
        invalid_date = datetime.strptime("invalid_date", '%d.%m.%Y').date()
        print("  Обработка неверной даты -> Успешно")
    except ValueError as e:
        print(f"  Обработка неверной даты -> ValueError: {e}")
    
    # Обработка неверной группы крови
    valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    invalid_blood_type = "INVALID"
    if invalid_blood_type in valid_types:
        print("  Проверка неверной группы крови -> Валидна")
    else:
        print("  Проверка неверной группы крови -> Невалидна")
    
    # Обработка неверного пароля
    master_password = "doctor2024"
    wrong_password = "wrong_password"
    if wrong_password == master_password:
        print("  Проверка неверного пароля -> Правильный")
    else:
        print("  Проверка неверного пароля -> Неправильный")

if __name__ == '__main__':
    test_error_handling() 