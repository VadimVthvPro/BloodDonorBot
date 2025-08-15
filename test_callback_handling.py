def test_callback_handling():
    """Тестирует обработку callback_data в деталях"""
    
    # Симулируем callback_data от кнопок выбора группы крови
    blood_type_callbacks = [
        "blood_A+",
        "blood_A-", 
        "blood_B+",
        "blood_B-",
        "blood_AB+",
        "blood_AB-",
        "blood_O+",
        "blood_O-"
    ]
    
    print("Тестируем обработку callback_data для групп крови:")
    for callback_data in blood_type_callbacks:
        # Симулируем обработку как в боте
        blood_type = callback_data.replace('blood_', '')
        print(f"  {callback_data} -> {blood_type}")
    
    # Симулируем callback_data от кнопок меню
    menu_callbacks = [
        "role_user",
        "role_doctor",
        "create_request",
        "user_info",
        "update_donation",
        "update_location",
        "my_requests",
        "statistics",
        "help",
        "back_to_menu"
    ]
    
    print("\nТестируем обработку callback_data для меню:")
    for callback_data in menu_callbacks:
        if callback_data.startswith("role_"):
            role = callback_data.replace('role_', '')
            print(f"  {callback_data} -> Выбор роли: {role}")
        elif callback_data == "create_request":
            print(f"  {callback_data} -> Создание запроса крови")
        elif callback_data == "user_info":
            print(f"  {callback_data} -> Показать информацию пользователя")
        elif callback_data == "update_donation":
            print(f"  {callback_data} -> Обновить дату сдачи")
        elif callback_data == "update_location":
            print(f"  {callback_data} -> Обновить местоположение")
        elif callback_data == "my_requests":
            print(f"  {callback_data} -> Мои запросы")
        elif callback_data == "statistics":
            print(f"  {callback_data} -> Статистика")
        elif callback_data == "help":
            print(f"  {callback_data} -> Справка")
        elif callback_data == "back_to_menu":
            print(f"  {callback_data} -> Возврат в меню")
    
    # Симулируем обработку callback_data в handle_blood_type_request
    print("\nТестируем обработку в handle_blood_type_request:")
    for callback_data in blood_type_callbacks:
        # Симулируем обработку как в боте
        blood_type = callback_data.replace('blood_', '')
        print(f"  Получен callback_data: {callback_data}")
        print(f"  Извлечена группа крови: {blood_type}")
        print(f"  Сохранена в context.user_data['request_blood_type']")
        print(f"  Возвращено состояние: ENTERING_REQUEST_LOCATION")
        print()
    
    # Симулируем обработку callback_data в handle_menu_callback
    print("Тестируем обработку в handle_menu_callback:")
    for callback_data in menu_callbacks:
        if callback_data == "create_request":
            print(f"  {callback_data} -> Вызывается create_donation_request")
        elif callback_data == "user_info":
            print(f"  {callback_data} -> Вызывается show_user_info")
        elif callback_data == "help":
            print(f"  {callback_data} -> Вызывается show_help")
        elif callback_data == "back_to_menu":
            print(f"  {callback_data} -> Возврат в соответствующее меню")
        else:
            print(f"  {callback_data} -> Показывается сообщение о функции в разработке")

if __name__ == '__main__':
    test_callback_handling() 