def test_state_handling():
    """Тестирует обработку состояний ConversationHandler"""
    
    # Определяем состояния
    CHOOSING_ROLE, ENTERING_PASSWORD, ENTERING_BLOOD_TYPE, ENTERING_LOCATION, \
    ENTERING_LAST_DONATION, USER_MENU, DOCTOR_MENU, ENTERING_DONATION_REQUEST, \
    ENTERING_REQUEST_LOCATION, ENTERING_REQUEST_DATE = range(10)
    
    # Симулируем поток состояний для создания запроса крови
    state_flow = [
        ("start", "Пользователь запускает бота"),
        ("CHOOSING_ROLE", "Выбор роли (донор/врач)"),
        ("ENTERING_PASSWORD", "Ввод пароля"),
        ("DOCTOR_MENU", "Меню врача"),
        ("ENTERING_DONATION_REQUEST", "Создание запроса крови"),
        ("ENTERING_REQUEST_LOCATION", "Ввод местоположения"),
        ("ENTERING_REQUEST_DATE", "Ввод даты"),
        ("DOCTOR_MENU", "Возврат в меню врача")
    ]
    
    print("Поток состояний для создания запроса крови:")
    for i, (state, description) in enumerate(state_flow):
        print(f"  {i+1}. {state} - {description}")
    
    # Симулируем обработчики для каждого состояния
    handlers = {
        "CHOOSING_ROLE": "CallbackQueryHandler(choose_role)",
        "ENTERING_PASSWORD": "MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)",
        "ENTERING_BLOOD_TYPE": "MessageHandler(filters.TEXT & ~filters.COMMAND, handle_blood_type)",
        "ENTERING_LOCATION": "MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location)",
        "ENTERING_LAST_DONATION": "MessageHandler(filters.TEXT & ~filters.COMMAND, handle_last_donation)",
        "ENTERING_DONATION_REQUEST": "CallbackQueryHandler(handle_blood_type_request)",
        "ENTERING_REQUEST_LOCATION": "MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request_location)",
        "ENTERING_REQUEST_DATE": "MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request_date)",
        "USER_MENU": "CallbackQueryHandler(handle_menu_callback)",
        "DOCTOR_MENU": "CallbackQueryHandler(handle_menu_callback)"
    }
    
    print("\nОбработчики для каждого состояния:")
    for state, handler in handlers.items():
        print(f"  {state}: {handler}")
    
    # Симулируем переходы между состояниями
    transitions = [
        ("start", "CHOOSING_ROLE"),
        ("CHOOSING_ROLE", "ENTERING_PASSWORD"),
        ("ENTERING_PASSWORD", "DOCTOR_MENU"),  # для врача
        ("DOCTOR_MENU", "ENTERING_DONATION_REQUEST"),
        ("ENTERING_DONATION_REQUEST", "ENTERING_REQUEST_LOCATION"),
        ("ENTERING_REQUEST_LOCATION", "ENTERING_REQUEST_DATE"),
        ("ENTERING_REQUEST_DATE", "DOCTOR_MENU")
    ]
    
    print("\nПереходы между состояниями:")
    for i, (from_state, to_state) in enumerate(transitions):
        print(f"  {i+1}. {from_state} -> {to_state}")

if __name__ == '__main__':
    test_state_handling() 