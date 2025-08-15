# 🚀 Быстрый запуск BloodDonorBot

## ⚡ Минимальная настройка для тестирования

### 1. Установка зависимостей
```bash
pip3 install -r requirements.txt
```

### 2. Создание файла настроек
```bash
cp env_example.txt .env
```

Отредактируйте файл `.env`:
```env
TELEGRAM_TOKEN=your_bot_token_here
DB_HOST=localhost
DB_NAME=blood_donor_bot
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

### 3. Запуск тестов
```bash
python3 simple_test.py
```

### 4. Запуск бота
```bash
python3 bot.py
```

## 📋 Что нужно для полной работы

### Обязательно:
- ✅ Python 3.8+
- ✅ Telegram Bot Token (от @BotFather)
- ✅ PostgreSQL (для полной функциональности)

### Опционально:
- 🔧 Настроенная база данных PostgreSQL
- 🌐 Домен для веб-интерфейса
- 📊 Система мониторинга

## 🎯 Основные команды

| Команда | Описание |
|---------|----------|
| `python3 simple_test.py` | Запуск тестов без БД |
| `python3 test_bot.py` | Полные тесты с БД |
| `python3 bot.py` | Запуск бота |
| `psql -f create_database.sql` | Создание БД |

## 🔧 Настройка базы данных

### Быстрый способ (Docker):
```bash
# Установка PostgreSQL в Docker
docker run --name postgres-blood-donor \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=blood_donor_bot \
  -p 5432:5432 \
  -d postgres:13

# Создание таблиц
docker exec -i postgres-blood-donor psql -U postgres -d blood_donor_bot < create_database.sql
```

### Стандартный способ:
```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Создание пользователя и БД
sudo -u postgres psql
CREATE USER blood_donor_user WITH PASSWORD 'your_password';
CREATE DATABASE blood_donor_bot OWNER blood_donor_user;
GRANT ALL PRIVILEGES ON DATABASE blood_donor_bot TO blood_donor_user;
\q

# Создание таблиц
psql -U blood_donor_user -d blood_donor_bot -f create_database.sql
```

## 🧪 Тестирование

### Упрощенные тесты (без БД):
```bash
python3 simple_test.py
```

### Полные тесты (с БД):
```bash
python3 test_bot.py
```

## 📱 Создание Telegram бота

1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

## 🚨 Устранение проблем

### Ошибка "ModuleNotFoundError":
```bash
pip3 install -r requirements.txt
```

### Ошибка подключения к БД:
- Проверьте, что PostgreSQL запущен
- Проверьте настройки в `.env`
- Убедитесь, что база данных создана

### Бот не отвечает:
- Проверьте токен в `.env`
- Убедитесь, что бот не заблокирован
- Проверьте логи в консоли

## 📊 Структура проекта

```
blood_donor_bot/
├── bot.py                 # Основной бот
├── user_functions.py      # Дополнительные функции
├── simple_test.py        # Упрощенные тесты
├── test_bot.py           # Полные тесты
├── create_database.sql   # SQL скрипт
├── requirements.txt      # Зависимости
├── env_example.txt      # Пример настроек
├── README.md            # Подробная документация
├── DEPLOYMENT.md        # Инструкции по развертыванию
├── PROJECT_SUMMARY.md   # Описание проекта
└── QUICK_START.md       # Это файл
```

## 🎓 Образовательная ценность

Этот проект поможет изучить:
- Python и асинхронное программирование
- Работу с Telegram Bot API
- Базы данных PostgreSQL
- Тестирование кода
- Развертывание приложений

## 🚀 Следующие шаги

1. **Изучите код** в файлах `bot.py` и `user_functions.py`
2. **Запустите тесты** для понимания функциональности
3. **Настройте базу данных** для полной работы
4. **Создайте бота** в Telegram
5. **Запустите проект** и протестируйте

---

**Удачи в изучении программирования! 🎉** 