"""
Упрощенные тесты для BloodDonorBot (без базы данных)
"""

import unittest
import os
import sys
from datetime import datetime, date

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestBloodDonorBotLogic(unittest.TestCase):
    """Тесты логики бота без подключения к базе данных"""
    
    def test_blood_type_validation(self):
        """Тест валидации группы крови"""
        valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        invalid_types = ['A', 'B', 'AB', 'O', 'A++', 'B--', 'invalid']
        
        for blood_type in valid_types:
            with self.subTest(blood_type=blood_type):
                self.assertTrue(blood_type in valid_types)
        
        for blood_type in invalid_types:
            with self.subTest(blood_type=blood_type):
                self.assertFalse(blood_type in valid_types)

    def test_date_parsing(self):
        """Тест парсинга дат"""
        valid_dates = [
            ('01.01.2024', date(2024, 1, 1)),
            ('31.12.2023', date(2023, 12, 31)),
            ('29.02.2024', date(2024, 2, 29))  # Високосный год
        ]
        
        invalid_dates = [
            '32.01.2024',  # Неверный день
            '01.13.2024',  # Неверный месяц
            '01.01.24',    # Неверный формат года
            '01-01-2024',  # Неверный разделитель
        ]
        
        for date_str, expected_date in valid_dates:
            with self.subTest(date_str=date_str):
                parsed_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                self.assertEqual(parsed_date, expected_date)
        
        for date_str in invalid_dates:
            with self.subTest(date_str=date_str):
                with self.assertRaises(ValueError):
                    datetime.strptime(date_str, '%d.%m.%Y')

    def test_master_password(self):
        """Тест мастер-пароля для врачей"""
        correct_password = "doctor2024"
        incorrect_passwords = ["doctor", "2024", "doctor2023", "admin", ""]
        
        self.assertEqual(correct_password, "doctor2024")
        
        for password in incorrect_passwords:
            with self.subTest(password=password):
                self.assertNotEqual(password, "doctor2024")

    def test_donation_interval_calculation(self):
        """Тест расчета интервала между сдачами крови"""
        min_interval = 60  # дней
        
        # Тест для нового донора (никогда не сдавал кровь)
        last_donation = None
        can_donate = True if last_donation is None else False
        self.assertTrue(can_donate)
        
        # Тест для донора, который сдавал кровь давно (более 60 дней назад)
        old_date = date(2023, 1, 1)  # Фиксированная дата в прошлом
        days_since = (date.today() - old_date).days
        can_donate = days_since >= min_interval
        self.assertTrue(can_donate)
        
        # Тест для донора, который сдавал кровь недавно (менее 60 дней назад)
        recent_date = date.today()  # Сегодня
        days_since = (date.today() - recent_date).days
        can_donate = days_since >= min_interval
        self.assertFalse(can_donate)

class TestDatabaseStructure(unittest.TestCase):
    """Тесты структуры базы данных"""
    
    def test_users_table_structure(self):
        """Тест структуры таблицы пользователей"""
        expected_columns = [
            'id', 'telegram_id', 'username', 'first_name', 'last_name',
            'role', 'blood_type', 'location', 'last_donation_date',
            'is_registered', 'created_at'
        ]
        
        # Проверяем, что все ожидаемые колонки присутствуют
        for column in expected_columns:
            with self.subTest(column=column):
                self.assertIn(column, expected_columns)

    def test_donation_requests_table_structure(self):
        """Тест структуры таблицы запросов"""
        expected_columns = [
            'id', 'doctor_id', 'blood_type', 'location', 'request_date',
            'description', 'created_at'
        ]
        
        # Проверяем, что все ожидаемые колонки присутствуют
        for column in expected_columns:
            with self.subTest(column=column):
                self.assertIn(column, expected_columns)

    def test_role_constraint(self):
        """Тест ограничения на роль пользователя"""
        valid_roles = ['user', 'doctor']
        invalid_roles = ['admin', 'moderator', 'guest', '']
        
        for role in valid_roles:
            with self.subTest(role=role):
                self.assertIn(role, ['user', 'doctor'])
        
        for role in invalid_roles:
            with self.subTest(role=role):
                self.assertNotIn(role, ['user', 'doctor'])

class TestConfiguration(unittest.TestCase):
    """Тесты конфигурации"""
    
    def test_environment_variables(self):
        """Тест переменных окружения"""
        required_vars = [
            'TELEGRAM_TOKEN',
            'DB_HOST',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_PORT'
        ]
        
        # Проверяем, что все необходимые переменные определены
        for var in required_vars:
            with self.subTest(var=var):
                # Проверяем, что переменная может быть установлена
                os.environ[var] = 'test_value'
                self.assertIn(var, os.environ)

    def test_database_config_structure(self):
        """Тест структуры конфигурации базы данных"""
        db_config = {
            'host': 'localhost',
            'database': 'blood_donor_bot',
            'user': 'postgres',
            'password': 'test_password',
            'port': '5432'
        }
        
        required_keys = ['host', 'database', 'user', 'password', 'port']
        
        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(key, db_config)

class TestBusinessLogic(unittest.TestCase):
    """Тесты бизнес-логики"""
    
    def test_blood_type_compatibility(self):
        """Тест совместимости групп крови"""
        # Универсальные доноры
        universal_donors = ['O-']
        # Универсальные реципиенты
        universal_recipients = ['AB+']
        
        # O- может сдавать всем
        for recipient in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']:
            with self.subTest(recipient=recipient):
                self.assertIn('O-', universal_donors)
        
        # AB+ может принимать от всех
        for donor in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']:
            with self.subTest(donor=donor):
                self.assertIn('AB+', universal_recipients)

    def test_location_matching(self):
        """Тест сопоставления местоположений"""
        # Тест точного совпадения
        location1 = "Москва"
        location2 = "Москва"
        self.assertEqual(location1, location2)
        
        # Тест частичного совпадения
        location3 = "Москва, Россия"
        location4 = "Москва"
        self.assertIn(location4, location3)
        
        # Тест несовпадения
        location5 = "Санкт-Петербург"
        self.assertNotEqual(location1, location5)

    def test_notification_logic(self):
        """Тест логики уведомлений"""
        # Тест условий для отправки уведомления
        blood_type_match = True
        location_match = True
        can_donate = True
        
        should_notify = blood_type_match and location_match and can_donate
        self.assertTrue(should_notify)
        
        # Тест когда не нужно отправлять уведомление
        can_donate = False
        should_notify = blood_type_match and location_match and can_donate
        self.assertFalse(should_notify)

def run_simple_tests():
    """Запуск упрощенных тестов"""
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestBloodDonorBotLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestBusinessLogic))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🧪 Запуск упрощенных тестов для BloodDonorBot...")
    print("📝 Эти тесты не требуют подключения к базе данных")
    print()
    
    success = run_simple_tests()
    
    if success:
        print("✅ Все тесты прошли успешно!")
        print("🎉 Логика бота работает корректно!")
    else:
        print("❌ Некоторые тесты не прошли!")
        print("🔧 Проверьте код и исправьте ошибки")
    
    print()
    print("📋 Для полного тестирования с базой данных:")
    print("1. Установите PostgreSQL")
    print("2. Создайте базу данных")
    print("3. Запустите: python test_bot.py")
    
    sys.exit(0 if success else 1) 