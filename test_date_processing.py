from datetime import datetime

def test_date_processing():
    """Тестирует обработку дат"""
    
    # Тестовые даты
    test_dates = [
        "30.07.2025",
        "01.01.2024",
        "15.12.2024",
        "invalid_date",
        "30/07/2025",
        "2025-07-30"
    ]
    
    print("Тестируем обработку дат:")
    for date_str in test_dates:
        try:
            parsed_date = datetime.strptime(date_str, '%d.%m.%Y').date()
            print(f"  '{date_str}' -> {parsed_date} ✅")
        except ValueError as e:
            print(f"  '{date_str}' -> Ошибка: {e} ❌")
    
    # Тестируем валидацию групп крови
    blood_types = [
        "A+",
        "A-", 
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
        "A",
        "B",
        "AB",
        "O"
    ]
    
    valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    print("\nТестируем валидацию групп крови:")
    for blood_type in blood_types:
        if blood_type in valid_types:
            print(f"  '{blood_type}' -> Валидна ✅")
        else:
            print(f"  '{blood_type}' -> Невалидна ❌")

if __name__ == '__main__':
    test_date_processing() 