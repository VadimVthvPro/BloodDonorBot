import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

def test_notification_handling():
    """Тестирует обработку уведомлений в деталях"""
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
        
        # Проверяем доноров в системе
        cursor.execute("""
            SELECT telegram_id, first_name, blood_type, last_donation_date 
            FROM users 
            WHERE role = 'user' AND is_registered = TRUE
            ORDER BY blood_type, first_name
        """)
        
        donors = cursor.fetchall()
        print(f"\nНайдено доноров: {len(donors)}")
        
        # Группируем по группам крови
        blood_type_groups = {}
        for donor in donors:
            blood_type = donor['blood_type']
            if blood_type not in blood_type_groups:
                blood_type_groups[blood_type] = []
            blood_type_groups[blood_type].append(donor)
        
        print("\nДоноры по группам крови:")
        for blood_type, donors_list in blood_type_groups.items():
            print(f"  {blood_type}: {len(donors_list)} доноров")
            for donor in donors_list:
                last_donation = donor['last_donation_date']
                if last_donation:
                    days_since = (datetime.now().date() - last_donation).days
                    can_donate = days_since >= 60
                    status = "✅ Может сдавать" if can_donate else f"⏳ Подождать {60 - days_since} дней"
                else:
                    status = "✅ Может сдавать"
                print(f"    {donor['first_name']} (ID: {donor['telegram_id']}) - {status}")
        
        # Тестируем поиск доноров для конкретных групп крови
        test_blood_types = ["A+", "B+", "AB+", "O+"]
        
        print("\nТестируем поиск доноров для разных групп крови:")
        for blood_type in test_blood_types:
            cursor.execute("""
                SELECT telegram_id, first_name, last_donation_date 
                FROM users 
                WHERE blood_type = %s AND role = 'user' AND is_registered = TRUE
            """, (blood_type,))
            
            test_donors = cursor.fetchall()
            print(f"\n  Группа {blood_type}: {len(test_donors)} доноров")
            
            eligible_donors = 0
            for donor in test_donors:
                can_donate = True
                if donor['last_donation_date']:
                    days_since = (datetime.now().date() - donor['last_donation_date']).days
                    can_donate = days_since >= 60
                
                if can_donate:
                    eligible_donors += 1
                    print(f"    {donor['first_name']} (ID: {donor['telegram_id']}) - получит уведомление ✅")
                else:
                    print(f"    {donor['first_name']} (ID: {donor['telegram_id']}) - не получит уведомление ⏳")
            
            print(f"    Всего подходящих доноров: {eligible_donors}")
        
        # Симулируем создание уведомления
        print("\nТестируем создание уведомления:")
        test_blood_type = "A+"
        test_location = "Москва"
        test_date = datetime.now().date()
        
        message = f"""
🩸 СРОЧНО НУЖНА КРОВЬ!

Группа крови: {test_blood_type}
📍 Местоположение: {test_location}
📅 Дата: {test_date.strftime('%d.%m.%Y')}

Если вы можете помочь, пожалуйста, свяжитесь с медицинским учреждением.

Спасибо за вашу готовность помочь! ❤️
        """
        
        print(f"Создано уведомление для группы {test_blood_type}:")
        print(message)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_notification_handling() 