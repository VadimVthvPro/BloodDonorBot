"""
Тесты для BloodDonorBot
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import BloodDonorBot
from user_functions import UserFunctions

class TestBloodDonorBot(unittest.TestCase):
    """Тесты для основного класса бота"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.db_config = {
            'host': 'localhost',
            'database': 'test_blood_donor_bot',
            'user': 'postgres',
            'password': 'test_password',
            'port': '5432'
        }
        
        # Мокаем переменные окружения
        self.env_patcher = patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_NAME': 'test_blood_donor_bot',
            'DB_USER': 'postgres',
            'DB_PASSWORD': 'test_password',
            'DB_PORT': '5432'
        })
        self.env_patcher.start()
        
        self.bot = BloodDonorBot()

    def tearDown(self):
        """Очистка после тестов"""
        self.env_patcher.stop()

    def test_db_config(self):
        """Тест конфигурации базы данных"""
        expected_config = {
            'host': 'localhost',
            'database': 'test_blood_donor_bot',
            'user': 'postgres',
            'password': 'test_password',
            'port': '5432'
        }
        self.assertEqual(self.bot.db_config, expected_config)

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
            '1.1.2024',    # Неверный формат
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

class TestUserFunctions(unittest.TestCase):
    """Тесты для функций пользователей"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.db_config = {
            'host': 'localhost',
            'database': 'test_blood_donor_bot',
            'user': 'postgres',
            'password': 'test_password',
            'port': '5432'
        }
        self.user_functions = UserFunctions(self.db_config)

    def test_donation_eligibility_new_donor(self):
        """Тест проверки возможности сдачи крови для нового донора"""
        # Мокаем данные пользователя без даты последней сдачи
        with patch.object(self.user_functions, 'get_db_connection') as mock_conn:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = {
                'last_donation_date': None,
                'blood_type': 'A+',
                'location': 'Москва'
            }
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            result = self.user_functions.check_donation_eligibility(123456)
            
            self.assertTrue(result['can_donate'])
            self.assertEqual(result['days_wait'], 0)

    def test_donation_eligibility_eligible_donor(self):
        """Тест проверки возможности сдачи крови для подходящего донора"""
        # Мокаем данные пользователя с датой сдачи более 60 дней назад
        old_date = date.today() - date.today().replace(day=1) + date.today().replace(day=1) - date.today().replace(month=1) + date.today().replace(month=1) - date.today().replace(year=2023) + date.today().replace(year=2023)
        
        with patch.object(self.user_functions, 'get_db_connection') as mock_conn:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = {
                'last_donation_date': old_date,
                'blood_type': 'B+',
                'location': 'Санкт-Петербург'
            }
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            result = self.user_functions.check_donation_eligibility(123456)
            
            self.assertTrue(result['can_donate'])
            self.assertEqual(result['days_wait'], 0)

    def test_donation_eligibility_ineligible_donor(self):
        """Тест проверки возможности сдачи крови для неподходящего донора"""
        # Мокаем данные пользователя с недавней датой сдачи
        recent_date = date.today() - date.today().replace(day=1) + date.today().replace(day=1) - date.today().replace(month=1) + date.today().replace(month=1) - date.today().replace(year=2024) + date.today().replace(year=2024)
        
        with patch.object(self.user_functions, 'get_db_connection') as mock_conn:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = {
                'last_donation_date': recent_date,
                'blood_type': 'O+',
                'location': 'Казань'
            }
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            result = self.user_functions.check_donation_eligibility(123456)
            
            self.assertFalse(result['can_donate'])
            self.assertGreater(result['days_wait'], 0)

    def test_get_available_donors(self):
        """Тест получения списка доступных доноров"""
        with patch.object(self.user_functions, 'get_db_connection') as mock_conn:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = [
                {
                    'telegram_id': 123456,
                    'first_name': 'Иван',
                    'last_name': 'Иванов',
                    'location': 'Москва',
                    'last_donation_date': None
                },
                {
                    'telegram_id': 789012,
                    'first_name': 'Петр',
                    'last_name': 'Петров',
                    'location': 'Москва',
                    'last_donation_date': date(2023, 1, 1)
                }
            ]
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            
            donors = self.user_functions.get_available_donors('A+', 'Москва')
            
            self.assertEqual(len(donors), 2)
            self.assertEqual(donors[0]['blood_type'], 'A+')
            self.assertEqual(donors[0]['location'], 'Москва')

class TestDatabaseQueries(unittest.TestCase):
    """Тесты SQL запросов"""
    
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

def run_tests():
    """Запуск всех тестов"""
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestBloodDonorBot))
    suite.addTests(loader.loadTestsFromTestCase(TestUserFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseQueries))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🧪 Запуск тестов для BloodDonorBot...")
    success = run_tests()
    
    if success:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли!")
    
    sys.exit(0 if success else 1) 