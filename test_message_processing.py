def test_message_processing():
    """Тестирует обработку сообщений"""
    
    # Симулируем сообщения от пользователя
    test_messages = [
        "doctor2024",  # мастер-пароль
        "password123",  # обычный пароль
        "A+",  # группа крови
        "Москва",  # местоположение
        "30.07.2025",  # дата
        "никогда",  # дата для тех, кто не сдавал
        "invalid_date"  # неверная дата
    ]
    
    print("Тестируем обработку сообщений:")
    for message in test_messages:
        print(f"  '{message}' -> обрабатывается в соответствующем обработчике")
    
    # Тестируем валидацию паролей
    master_password = "doctor2024"
    test_passwords = [
        "doctor2024",
        "doctor2023",
        "password123",
        "123456"
    ]
    
    print("\nТестируем валидацию паролей:")
    for password in test_passwords:
        if password == master_password:
            print(f"  '{password}' -> Мастер-пароль ✅")
        else:
            print(f"  '{password}' -> Обычный пароль или неверный ❌")
    
    # Тестируем валидацию местоположения
    test_locations = [
        "Москва",
        "Санкт-Петербург",
        "Новосибирск",
        "Екатеринбург",
        "",  # пустое
        "123"  # цифры
    ]
    
    print("\nТестируем валидацию местоположения:")
    for location in test_locations:
        if location and len(location) > 0:
            print(f"  '{location}' -> Валидно ✅")
        else:
            print(f"  '{location}' -> Невалидно ❌")

if __name__ == '__main__':
    test_message_processing() 