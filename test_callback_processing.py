def test_callback_processing():
    """Тестирует обработку callback_data"""
    
    # Симулируем callback_data от кнопок
    test_callback_data = [
        "blood_A+",
        "blood_A-", 
        "blood_B+",
        "blood_B-",
        "blood_AB+",
        "blood_AB-",
        "blood_O+",
        "blood_O-"
    ]
    
    print("Тестируем обработку callback_data:")
    for callback_data in test_callback_data:
        # Симулируем обработку как в боте
        blood_type = callback_data.replace('blood_', '')
        print(f"  {callback_data} -> {blood_type}")
    
    # Тестируем обработку меню
    menu_callbacks = [
        "create_request",
        "user_info", 
        "help",
        "back_to_menu"
    ]
    
    print("\nТестируем обработку меню:")
    for callback_data in menu_callbacks:
        print(f"  {callback_data} -> обрабатывается в handle_menu_callback")
    
    # Тестируем состояния
    states = {
        "CHOOSING_ROLE": 0,
        "ENTERING_PASSWORD": 1,
        "ENTERING_BLOOD_TYPE": 2,
        "ENTERING_LOCATION": 3,
        "ENTERING_LAST_DONATION": 4,
        "USER_MENU": 5,
        "DOCTOR_MENU": 6,
        "ENTERING_DONATION_REQUEST": 7,
        "ENTERING_REQUEST_LOCATION": 8,
        "ENTERING_REQUEST_DATE": 9
    }
    
    print("\nСостояния ConversationHandler:")
    for state_name, state_value in states.items():
        print(f"  {state_name}: {state_value}")

if __name__ == '__main__':
    test_callback_processing() 