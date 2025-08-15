import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_bot():
    """Тестирует подключение к боту"""
    bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
    
    try:
        # Получаем информацию о боте
        me = await bot.get_me()
        print(f"✅ Бот подключен: {me.first_name} (@{me.username})")
        
        # Проверяем, что токен правильный
        print(f"Токен: {os.getenv('TELEGRAM_TOKEN')[:20]}...")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к боту: {e}")

if __name__ == '__main__':
    asyncio.run(test_bot()) 