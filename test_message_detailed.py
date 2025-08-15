from datetime import datetime

def test_message_detailed():
    """Детально тестирует обработку сообщений"""
    
    # Симулируем сообщения от пользователя
    test_messages = [
        ("doctor2024", "Мастер-пароль для врача"),
        ("password123", "Обычный пароль для донора"),
        ("A+", "Группа крови"),
        ("Москва", "Местоположение"),
        ("30.07.2025", "Дата в правильном формате"),
        ("никогда", "Дата для тех, кто не сдавал кровь"),
        ("invalid_date", "Неверная дата")
    ]
    
    print("Тестируем обработку сообщений:")
    for message, description in test_messages:
        print(f"  '{message}' - {description}")
    
    # Тестируем валидацию паролей
    master_password = "doctor2024"
    test_passwords = [
        ("doctor2024", "Правильный мастер-пароль"),
        ("doctor2023", "Неверный мастер-пароль"),
        ("password123", "Обычный пароль"),
        ("123456", "Простой пароль")
    ]
    
    print("\nТестируем валидацию паролей:")
    for password, description in test_passwords:
        if password == master_password:
            print(f"  '{password}' - {description} ✅")
        else:
            print(f"  '{password}' - {description} ❌")
    
    # Тестируем валидацию групп крови
    valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    test_blood_types = [
        ("A+", "Правильная группа крови"),
        ("A-", "Правильная группа крови"),
        ("B+", "Правильная группа крови"),
        ("B-", "Правильная группа крови"),
        ("AB+", "Правильная группа крови"),
        ("AB-", "Правильная группа крови"),
        ("O+", "Правильная группа крови"),
        ("O-", "Правильная группа крови"),
        ("A", "Неверная группа крови"),
        ("B", "Неверная группа крови"),
        ("AB", "Неверная группа крови"),
        ("O", "Неверная группа крови"),
        ("INVALID", "Неверная группа крови")
    ]
    
    print("\nТестируем валидацию групп крови:")
    for blood_type, description in test_blood_types:
        if blood_type in valid_types:
            print(f"  '{blood_type}' - {description} ✅")
        else:
            print(f"  '{blood_type}' - {description} ❌")
    
    # Тестируем валидацию дат
    test_dates = [
        ("30.07.2025", "Правильная дата"),
        ("01.01.2024", "Правильная дата"),
        ("15.12.2024", "Правильная дата"),
        ("никогда", "Специальное значение"),
        ("invalid_date", "Неверная дата"),
        ("30/07/2025", "Неверный формат"),
        ("2025-07-30", "Неверный формат")
    ]
    
    print("\nТестируем валидацию дат:")
    for date_str, description in test_dates:
        if date_str.lower() == 'никогда':
            print(f"  '{date_str}' - {description} ✅")
        else:
            try:
                parsed_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                print(f"  '{date_str}' - {description} -> {parsed_date} ✅")
            except ValueError:
                print(f"  '{date_str}' - {description} -> Ошибка парсинга ❌")
    
    # Тестируем валидацию местоположения
    test_locations = [
        ("Москва", "Правильное местоположение"),
        ("Санкт-Петербург", "Правильное местоположение"),
        ("Новосибирск", "Правильное местоположение"),
        ("Екатеринбург", "Правильное местоположение"),
        ("", "Пустое местоположение"),
        ("123", "Цифровое местоположение"),
        ("A", "Короткое местоположение")
    ]
    
    print("\nТестируем валидацию местоположения:")
    for location, description in test_locations:
        if location and len(location) > 0:
            print(f"  '{location}' - {description} ✅")
        else:
            print(f"  '{location}' - {description} ❌")

if __name__ == '__main__':
    test_message_detailed() 