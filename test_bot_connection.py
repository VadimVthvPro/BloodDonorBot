import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_bot_connection():
    """Тестирует подключение к боту"""
    bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
    
    try:
        # Получаем информацию о боту
        me = await bot.get_me()
        print(f"✅ Бот подключен: {me.first_name} (@{me.username})")
        print(f"ID бота: {me.id}")
        
        # Проверяем, что токен правильный
        print(f"Токен: {os.getenv('TELEGRAM_TOKEN')[:20]}...")
        
        # Пробуем отправить тестовое сообщение (если указан chat_id)
        # Для тестирования нужно указать ваш chat_id
        # test_chat_id = 123456789  # Замените на ваш chat_id
        # await bot.send_message(chat_id=test_chat_id, text="Тестовое сообщение от бота")
        # print("✅ Тестовое сообщение отправлено")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к боту: {e}")

if __name__ == '__main__':
    asyncio.run(test_bot_connection()) 