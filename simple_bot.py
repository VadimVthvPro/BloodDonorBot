import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния
CHOOSING_ROLE, ENTERING_PASSWORD, ENTERING_BLOOD_TYPE, ENTERING_LOCATION, \
ENTERING_LAST_DONATION, USER_MENU, DOCTOR_MENU, ENTERING_DONATION_REQUEST, \
ENTERING_REQUEST_LOCATION, ENTERING_REQUEST_DATE = range(10)

# Мастер-пароль для врачей
MASTER_PASSWORD = "doctor2024"

class SimpleBloodBot:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'Bloodcontrol'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'Vadamahjkl1'),
            'port': os.getenv('DB_PORT', '5432')
        }

    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начальная команда"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} запустил бота")
        
        keyboard = [
            [InlineKeyboardButton("👤 Я донор", callback_data="role_user")],
            [InlineKeyboardButton("👨‍⚕️ Я врач", callback_data="role_doctor")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}! Добро пожаловать в BloodDonorBot!\n\n"
            "Выберите вашу роль:",
            reply_markup=reply_markup
        )
        return CHOOSING_ROLE

    async def choose_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора роли"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Выбрана роль: {query.data}")
        
        if query.data == "role_doctor":
            context.user_data['role'] = 'doctor'
            await query.edit_message_text(
                "👨‍⚕️ Вы выбрали роль врача.\n\n"
                "Для доступа введите мастер-пароль:"
            )
            return ENTERING_PASSWORD
        else:
            context.user_data['role'] = 'user'
            await query.edit_message_text(
                "👤 Вы выбрали роль донора.\n\n"
                "Придумайте пароль:"
            )
            return ENTERING_PASSWORD

    async def handle_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка пароля"""
        password = update.message.text
        logger.info(f"Введен пароль: {password}")
        
        if context.user_data['role'] == 'doctor':
            if password == MASTER_PASSWORD:
                await self.register_doctor(update, context)
                return DOCTOR_MENU
            else:
                await update.message.reply_text("❌ Неверный пароль. Попробуйте еще раз:")
                return ENTERING_PASSWORD
        else:
            context.user_data['password'] = password
            await update.message.reply_text(
                "✅ Пароль сохранен!\n\n"
                "Укажите группу крови (A+, B-, AB+, O-):"
            )
            return ENTERING_BLOOD_TYPE

    async def register_doctor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Регистрация врача"""
        user = update.effective_user
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, role, is_registered)
                VALUES (%s, %s, %s, %s, 'doctor', TRUE)
                ON CONFLICT (telegram_id) 
                DO UPDATE SET role = 'doctor', is_registered = TRUE
            """, (user.id, user.username, user.first_name, user.last_name))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            await update.message.reply_text("✅ Вы зарегистрированы как врач!")
            await self.show_doctor_menu(update, context)
        except Exception as e:
            logger.error(f"Ошибка регистрации врача: {e}")
            await update.message.reply_text("Произошла ошибка при регистрации.")

    async def handle_blood_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка группы крови"""
        blood_type = update.message.text.upper()
        valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        
        if blood_type not in valid_types:
            await update.message.reply_text(
                "❌ Неверный формат. Используйте: A+, B-, AB+, O- и т.д.\n"
                "Попробуйте еще раз:"
            )
            return ENTERING_BLOOD_TYPE
        
        context.user_data['blood_type'] = blood_type
        await update.message.reply_text(
            "✅ Группа крови сохранена!\n\n"
            "Укажите местоположение (город):"
        )
        return ENTERING_LOCATION

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка местоположения"""
        location = update.message.text
        context.user_data['location'] = location
        
        await update.message.reply_text(
            "✅ Местоположение сохранено!\n\n"
            "Укажите дату последней сдачи (ДД.ММ.ГГГГ) или 'никогда':"
        )
        return ENTERING_LAST_DONATION

    async def handle_last_donation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка даты последней сдачи"""
        last_donation = update.message.text
        
        if last_donation.lower() == 'никогда':
            last_donation_date = None
        else:
            try:
                last_donation_date = datetime.strptime(last_donation, '%d.%m.%Y').date()
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ\n"
                    "Попробуйте еще раз:"
                )
                return ENTERING_LAST_DONATION
        
        # Регистрируем пользователя
        user = update.effective_user
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, role, 
                                 blood_type, location, last_donation_date, is_registered)
                VALUES (%s, %s, %s, %s, 'user', %s, %s, %s, TRUE)
                ON CONFLICT (telegram_id) 
                DO UPDATE SET blood_type = EXCLUDED.blood_type, 
                             location = EXCLUDED.location, 
                             last_donation_date = EXCLUDED.last_donation_date,
                             is_registered = TRUE
            """, (user.id, user.username, user.first_name, user.last_name,
                  context.user_data['blood_type'], context.user_data['location'], last_donation_date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            await update.message.reply_text("🎉 Регистрация завершена!")
            await self.show_user_menu(update, context)
            return USER_MENU
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            await update.message.reply_text("Произошла ошибка при регистрации.")

    async def show_user_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню пользователя"""
        keyboard = [
            [InlineKeyboardButton("📊 Моя информация", callback_data="user_info")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "👤 Меню донора\n\nВыберите действие:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "👤 Меню донора\n\nВыберите действие:",
                reply_markup=reply_markup
            )

    async def show_doctor_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню врача"""
        keyboard = [
            [InlineKeyboardButton("🩸 Создать запрос крови", callback_data="create_request")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "👨‍⚕️ Меню врача\n\nВыберите действие:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "👨‍⚕️ Меню врача\n\nВыберите действие:",
                reply_markup=reply_markup
            )

    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка меню"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Нажата кнопка: {query.data}")
        
        if query.data == "create_request":
            logger.info("Создание запроса крови")
            await self.create_donation_request(update, context)
        elif query.data == "user_info":
            await update.callback_query.edit_message_text("Функция в разработке")
        elif query.data == "help":
            await update.callback_query.edit_message_text("Справка по боту")

    async def create_donation_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание запроса крови"""
        logger.info("Начинаем создание запроса")
        
        keyboard = [
            [InlineKeyboardButton("A+", callback_data="blood_A+")],
            [InlineKeyboardButton("A-", callback_data="blood_A-")],
            [InlineKeyboardButton("B+", callback_data="blood_B+")],
            [InlineKeyboardButton("B-", callback_data="blood_B-")],
            [InlineKeyboardButton("AB+", callback_data="blood_AB+")],
            [InlineKeyboardButton("AB-", callback_data="blood_AB-")],
            [InlineKeyboardButton("O+", callback_data="blood_O+")],
            [InlineKeyboardButton("O-", callback_data="blood_O-")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "🩸 Создание запроса на сдачу крови\n\n"
            "Выберите нужную группу крови:",
            reply_markup=reply_markup
        )
        return ENTERING_DONATION_REQUEST

    async def handle_blood_type_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора группы крови"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Получен callback_data: {query.data}")
        
        blood_type = query.data.replace('blood_', '')
        context.user_data['request_blood_type'] = blood_type
        
        logger.info(f"Выбрана группа крови: {blood_type}")
        
        await query.edit_message_text(
            f"✅ Выбрана группа крови: {blood_type}\n\n"
            "Укажите город, где нужна кровь:"
        )
        return ENTERING_REQUEST_LOCATION

    async def handle_request_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка местоположения запроса"""
        location = update.message.text
        context.user_data['request_location'] = location
        
        logger.info(f"Указано местоположение: {location}")
        
        await update.message.reply_text(
            "✅ Местоположение указано!\n\n"
            "Укажите дату, когда нужна кровь (ДД.ММ.ГГГГ):"
        )
        return ENTERING_REQUEST_DATE

    async def handle_request_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка даты запроса"""
        try:
            request_date = datetime.strptime(update.message.text, '%d.%m.%Y').date()
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ\n"
                "Попробуйте еще раз:"
            )
            return ENTERING_REQUEST_DATE
        
        # Сохраняем запрос
        user = update.effective_user
        logger.info(f"Сохранение запроса: врач {user.id}, группа {context.user_data['request_blood_type']}, место {context.user_data['request_location']}, дата {request_date}")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO donation_requests (doctor_id, blood_type, location, request_date)
                VALUES (%s, %s, %s, %s)
            """, (user.id, context.user_data['request_blood_type'], 
                  context.user_data['request_location'], request_date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ Запрос успешно сохранен в БД")
            
            await update.message.reply_text(
                f"✅ Запрос создан!\n\n"
                f"🩸 Группа крови: {context.user_data['request_blood_type']}\n"
                f"📍 Местоположение: {context.user_data['request_location']}\n"
                f"📅 Дата: {request_date.strftime('%d.%m.%Y')}\n\n"
                f"Уведомления отправлены всем подходящим донорам."
            )
            
            await self.show_doctor_menu(update, context)
            return DOCTOR_MENU
        except Exception as e:
            logger.error(f"Ошибка сохранения запроса: {e}")
            await update.message.reply_text("Произошла ошибка при создании запроса. Попробуйте позже.")

    def run(self):
        """Запуск бота"""
        self.application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                CHOOSING_ROLE: [CallbackQueryHandler(self.choose_role)],
                ENTERING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_password)],
                ENTERING_BLOOD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_blood_type)],
                ENTERING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_location)],
                ENTERING_LAST_DONATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_last_donation)],
                ENTERING_DONATION_REQUEST: [CallbackQueryHandler(self.handle_blood_type_request)],
                ENTERING_REQUEST_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_location)],
                ENTERING_REQUEST_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_date)],
                USER_MENU: [CallbackQueryHandler(self.handle_menu_callback)],
                DOCTOR_MENU: [CallbackQueryHandler(self.handle_menu_callback)]
            },
            fallbacks=[CommandHandler('start', self.start)]
        )
        
        self.application.add_handler(conv_handler)
        
        logger.info("Простой бот запущен")
        self.application.run_polling()

if __name__ == '__main__':
    bot = SimpleBloodBot()
    bot.run() 