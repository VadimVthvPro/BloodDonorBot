def test_callback_data():
    """Тестирует обработку callback_data"""
    test_data = "blood_A+"
    print(f"Тестовый callback_data: {test_data}")
    
    # Симулируем обработку
    blood_type = test_data.replace('blood_', '')
    print(f"Извлеченная группа крови: {blood_type}")
    
    # Проверяем все возможные варианты
    test_cases = [
        "blood_A+",
        "blood_A-", 
        "blood_B+",
        "blood_B-",
        "blood_AB+",
        "blood_AB-",
        "blood_O+",
        "blood_O-"
    ]
    
    print("\nТестируем все варианты:")
    for case in test_cases:
        extracted = case.replace('blood_', '')
        print(f"  {case} -> {extracted}")

if __name__ == '__main__':
    test_callback_data() 