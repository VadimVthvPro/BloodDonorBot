def test_states():
    """Тестирует состояния ConversationHandler"""
    
    # Определяем состояния
    CHOOSING_ROLE, ENTERING_PASSWORD, ENTERING_BLOOD_TYPE, ENTERING_LOCATION, \
    ENTERING_LAST_DONATION, USER_MENU, DOCTOR_MENU, ENTERING_DONATION_REQUEST, \
    ENTERING_REQUEST_LOCATION, ENTERING_REQUEST_DATE = range(10)
    
    print("Состояния ConversationHandler:")
    states = [
        ("CHOOSING_ROLE", "Выбор роли"),
        ("ENTERING_PASSWORD", "Ввод пароля"),
        ("ENTERING_BLOOD_TYPE", "Ввод группы крови"),
        ("ENTERING_LOCATION", "Ввод местоположения"),
        ("ENTERING_LAST_DONATION", "Ввод даты последней сдачи"),
        ("USER_MENU", "Меню пользователя"),
        ("DOCTOR_MENU", "Меню врача"),
        ("ENTERING_DONATION_REQUEST", "Создание запроса крови"),
        ("ENTERING_REQUEST_LOCATION", "Ввод местоположения запроса"),
        ("ENTERING_REQUEST_DATE", "Ввод даты запроса")
    ]
    
    for i, (state, description) in enumerate(states):
        print(f"  {i}. {state} - {description}")
    
    print("\nПоток для создания запроса крови:")
    flow = [
        "start -> CHOOSING_ROLE",
        "CHOOSING_ROLE -> ENTERING_PASSWORD", 
        "ENTERING_PASSWORD -> DOCTOR_MENU",
        "DOCTOR_MENU -> ENTERING_DONATION_REQUEST",
        "ENTERING_DONATION_REQUEST -> ENTERING_REQUEST_LOCATION",
        "ENTERING_REQUEST_LOCATION -> ENTERING_REQUEST_DATE",
        "ENTERING_REQUEST_DATE -> DOCTOR_MENU"
    ]
    
    for step in flow:
        print(f"  {step}")

if __name__ == '__main__':
    test_states() 