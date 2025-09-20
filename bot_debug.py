import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, \
    ConversationHandler
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

# Состояния для ConversationHandler
CHOOSING_ROLE, ENTERING_PASSWORD, ENTERING_BLOOD_TYPE, ENTERING_LOCATION, \
    ENTERING_LAST_DONATION, USER_MENU, DOCTOR_MENU, ENTERING_DONATION_REQUEST, \
    ENTERING_REQUEST_LOCATION, ENTERING_REQUEST_ADDRESS, ENTERING_REQUEST_HOSPITAL, \
    ENTERING_REQUEST_CONTACT, ENTERING_REQUEST_DATE, UPDATE_LOCATION, UPDATE_DONATION_DATE = range(15)

# Мастер-пароль для врачей
MASTER_PASSWORD = "doctor2024"


class BloodDonorBot:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'blood_donor_bot'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'vadamahjkl'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.application = None
        self.init_database()

    def get_db_connection(self):
        """Создает соединение с базой данных"""
        return psycopg2.connect(**self.db_config)

    def init_database(self):
        """Инициализирует базу данных"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Создание таблиц
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'doctor')),
                    blood_type VARCHAR(10),
                    location VARCHAR(255),
                    last_donation_date DATE,
                    is_registered BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS donation_requests (
                    id SERIAL PRIMARY KEY,
                    doctor_id BIGINT NOT NULL,
                    blood_type VARCHAR(10) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    address VARCHAR(255) NOT NULL,
                    request_date DATE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES users(telegram_id)
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()
            logger.info("База данных инициализирована успешно")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начальная команда бота"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.first_name}) запустил бота")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Проверяем, зарегистрирован ли пользователь
            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user.id,))
            existing_user = cursor.fetchone()

            if existing_user and existing_user['is_registered']:
                if existing_user['role'] == 'doctor':
                    await self.show_doctor_menu(update, context)
                    return DOCTOR_MENU
                else:
                    await self.show_user_menu(update, context)
                    return USER_MENU
            else:
                keyboard = [
                    [InlineKeyboardButton("👤 Я донор", callback_data="role_user")],
                    [InlineKeyboardButton("👨‍⚕️ Я врач", callback_data="role_doctor")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"👋 Привет, {user.first_name}! Добро пожаловать в BloodDonorBot!\n\n"
                    "Этот бот поможет связать доноров крови с медицинскими учреждениями.\n\n"
                    "Выберите вашу роль:",
                    reply_markup=reply_markup
                )

            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка в start: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

        return CHOOSING_ROLE

    async def choose_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора роли"""
        query = update.callback_query
        await query.answer()

        logger.info(f"Пользователь {update.effective_user.id} выбрал роль: {query.data}")

        if query.data == "role_user":
            context.user_data['role'] = 'user'
            # Сразу переходим к выбору группы крови через инлайн кнопки
            keyboard = [
                [InlineKeyboardButton("🩸 A+", callback_data="blood_A+"),
                 InlineKeyboardButton("🩸 A-", callback_data="blood_A-")],
                [InlineKeyboardButton("🩸 B+", callback_data="blood_B+"),
                 InlineKeyboardButton("🩸 B-", callback_data="blood_B-")],
                [InlineKeyboardButton("🩸 AB+", callback_data="blood_AB+"),
                 InlineKeyboardButton("🩸 AB-", callback_data="blood_AB-")],
                [InlineKeyboardButton("🩸 O+", callback_data="blood_O+"),
                 InlineKeyboardButton("🩸 O-", callback_data="blood_O-")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "👤 Отлично! Вы выбрали роль донора.\n\n"
                "🩸 Выберите вашу группу крови:",
                reply_markup=reply_markup
            )
            return ENTERING_BLOOD_TYPE
        elif query.data == "role_doctor":
            context.user_data['role'] = 'doctor'
            await query.edit_message_text(
                "👨‍⚕️ Вы выбрали роль врача.\n\n"
                "Для доступа к функциям врача введите мастер-пароль:"
            )
            return ENTERING_PASSWORD

    async def handle_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода пароля"""
        password = update.message.text
        logger.info(f"Пользователь {update.effective_user.id} ввел пароль")

        if context.user_data['role'] == 'doctor':
            if password == MASTER_PASSWORD:
                await self.register_doctor(update, context)
                return DOCTOR_MENU
            else:
                await update.message.reply_text(
                    "❌ Неверный мастер-пароль. Попробуйте еще раз:"
                )
                return ENTERING_PASSWORD
        else:
            # Для обычных пользователей сохраняем пароль
            context.user_data['password'] = password
            await update.message.reply_text(
                "✅ Пароль сохранен!\n\n"
                "Теперь укажите вашу группу крови (например: A+, B-, AB+, O-):"
            )
            return ENTERING_BLOOD_TYPE

    async def register_doctor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Регистрация врача"""
        user = update.effective_user
        logger.info(f"Регистрация врача: {user.id}")

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

            await update.message.reply_text("✅ Вы успешно зарегистрированы как врач!")
            await self.show_doctor_menu(update, context)
        except Exception as e:
            logger.error(f"Ошибка регистрации врача: {e}")
            await update.message.reply_text("Произошла ошибка при регистрации.")

    async def handle_blood_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора группы крови через инлайн кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('blood_'):
            blood_type = query.data.replace('blood_', '')
            context.user_data['blood_type'] = blood_type
            
            await query.edit_message_text(
                f"✅ Группа крови {blood_type} выбрана!\n\n"
                "📍 Теперь укажите ваше местоположение (город):"
            )
            return ENTERING_LOCATION
        
        # Для обратной совместимости - если кто-то введет текстом
        blood_type = update.message.text.upper() if update.message else ""
        valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

        if blood_type not in valid_types:
            await update.message.reply_text(
                "❌ Неверный формат группы крови. Используйте кнопки выше для выбора."
            )
            return ENTERING_BLOOD_TYPE

        context.user_data['blood_type'] = blood_type
        await update.message.reply_text(
            "✅ Группа крови сохранена!\n\n"
            "Теперь укажите ваше местоположение (город):"
        )
        return ENTERING_LOCATION

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода местоположения"""
        location = update.message.text
        context.user_data['location'] = location

        await update.message.reply_text(
            "✅ Местоположение сохранено!\n\n"
            "Укажите дату последней сдачи крови в формате ДД.ММ.ГГГГ\n"
            "(или напишите 'никогда', если вы еще не сдавали кровь):"
        )
        return ENTERING_LAST_DONATION

    async def handle_last_donation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода даты последней сдачи крови"""
        last_donation = update.message.text

        if last_donation.lower() == 'никогда':
            last_donation_date = None
        else:
            try:
                last_donation_date = datetime.strptime(last_donation, '%d.%m.%Y').date()
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
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

            await update.message.reply_text(
                "🎉 Регистрация завершена! Вы успешно зарегистрированы как донор крови.\n\n"
                "Теперь вы будете получать уведомления о необходимости сдачи крови в вашем регионе."
            )
            await self.show_user_menu(update, context)
            return USER_MENU
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            await update.message.reply_text("Произошла ошибка при регистрации.")

    async def show_user_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает меню пользователя"""
        keyboard = [
            [InlineKeyboardButton("📊 Моя информация", callback_data="user_info")],
            [InlineKeyboardButton("🩸 Мои донации", callback_data="my_donations")],
            [InlineKeyboardButton("📅 Обновить дату сдачи", callback_data="update_donation")],
            [InlineKeyboardButton("📍 Изменить местоположение", callback_data="update_location")],
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
        """Показывает меню врача"""
        keyboard = [
            [InlineKeyboardButton("🩸 Создать запрос крови", callback_data="create_request")],
            [InlineKeyboardButton("📋 Мои запросы", callback_data="my_requests")],
            [InlineKeyboardButton("👥 Отклики доноров", callback_data="donor_responses")],
            [InlineKeyboardButton("📊 Статистика", callback_data="statistics")],
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
        """Обработка нажатий в меню"""
        query = update.callback_query
        await query.answer()

        logger.info(f"Пользователь {update.effective_user.id} нажал: {query.data}")

        if query.data == "user_info":
            await self.show_user_info(update, context)
            return USER_MENU
        elif query.data == "my_donations":
            await self.show_my_donations(update, context)
            return USER_MENU
        elif query.data == "update_donation":
            await query.edit_message_text(
                "📅 Обновление даты последней сдачи крови\n\n"
                "Введите дату последней сдачи крови в формате ДД.ММ.ГГГГ\n"
                "(или напишите 'никогда', если вы еще не сдавали кровь):"
            )
            return UPDATE_DONATION_DATE
        elif query.data == "update_location":
            await query.edit_message_text(
                "📍 Обновление местоположения\n\n"
                "Введите новое местоположение (город):"
            )
            return UPDATE_LOCATION
        elif query.data == "create_request":
            logger.info("Создание запроса крови")
            await self.create_donation_request(update, context)
            return ENTERING_DONATION_REQUEST
        elif query.data == "my_requests":
            await self.show_my_requests(update, context)
            return DOCTOR_MENU
        elif query.data == "donor_responses":
            await self.show_donor_responses(update, context)
            return DOCTOR_MENU
        elif query.data == "statistics":
            await self.show_statistics(update, context)
            return DOCTOR_MENU
        elif query.data == "help":
            await self.show_help(update, context)
            if self.is_doctor(update.effective_user.id):
                return DOCTOR_MENU
            else:
                return USER_MENU
        elif query.data.startswith("respond_"):
            # Обработка отклика донора
            await self.handle_donor_response(update, context)
            # После отклика показываем меню донора
            await self.show_user_menu(update, context)
            return USER_MENU
        elif query.data == "back_to_menu":
            user = update.effective_user
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (user.id,))
                user_data = cursor.fetchone()
                cursor.close()
                conn.close()

                if user_data and user_data['role'] == 'doctor':
                    await self.show_doctor_menu(update, context)
                    return DOCTOR_MENU
                else:
                    await self.show_user_menu(update, context)
                    return USER_MENU
            except Exception as e:
                logger.error(f"Ошибка при возврате в меню: {e}")
                return CHOOSING_ROLE

    def is_doctor(self, user_id):
        """Проверяет, является ли пользователь врачом"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            return user_data and user_data['role'] == 'doctor'
        except:
            return False

    async def show_user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает информацию о пользователе"""
        user = update.effective_user
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user.id,))
            user_data = cursor.fetchone()

            if user_data:
                last_donation = user_data['last_donation_date']
                if last_donation:
                    days_since = (datetime.now().date() - last_donation).days
                    can_donate = days_since >= 60
                    status = "✅ Можете сдавать кровь" if can_donate else f"⏳ Подождите еще {60 - days_since} дней"
                else:
                    status = "✅ Можете сдавать кровь"

                info_text = f"""
📊 Ваша информация:

🩸 Группа крови: {user_data['blood_type']}
📍 Местоположение: {user_data['location']}
📅 Последняя сдача: {last_donation.strftime('%d.%m.%Y') if last_donation else 'Не сдавали'}
🔄 Статус: {status}
                """
            else:
                info_text = "❌ Информация не найдена"

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(info_text, reply_markup=reply_markup)

            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка показа информации пользователя: {e}")

    async def show_my_donations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает донации пользователя"""
        user = update.effective_user
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Получаем все отклики пользователя
            cursor.execute("""
                SELECT dr.blood_type, dr.hospital_name, dr.location, dr.address, 
                       dr.contact_info, dr.request_date, resp.responded_at,
                       dr.created_at
                FROM donor_responses resp
                JOIN donation_requests dr ON resp.request_id = dr.id
                WHERE resp.donor_id = %s
                ORDER BY resp.responded_at DESC
                LIMIT 10
            """, (user.id,))

            donations = cursor.fetchall()

            if donations:
                text = "🩸 Мои донации (отклики):\n\n"
                for i, donation in enumerate(donations, 1):
                    status_emoji = "📅" if donation['request_date'] >= datetime.now().date() else "✅"
                    
                    text += f"{i}. {status_emoji} 🩸 {donation['blood_type']} | 📍 {donation['location']}\n"
                    text += f"🏥 {donation['hospital_name']}\n"
                    text += f"📍 {donation['address']}\n"
                    text += f"📞 {donation['contact_info']}\n"
                    text += f"📅 Дата донации: {donation['request_date'].strftime('%d.%m.%Y')}\n"
                    text += f"🕒 Откликнулись: {donation['responded_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            else:
                text = "У вас пока нет откликов на донации.\n\nКогда появятся запросы крови вашей группы, вы получите уведомления."

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка показа донаций пользователя: {e}")
            await update.callback_query.edit_message_text("Произошла ошибка при загрузке донаций.")

    async def update_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обновляет местоположение пользователя"""
        new_location = update.message.text
        user = update.effective_user
        logger.info(f"Обновление местоположения для пользователя {user.id}: {new_location}")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users
                SET location = %s
                WHERE telegram_id = %s
            """, (new_location, user.id))

            conn.commit()
            cursor.close()
            conn.close()

            await update.message.reply_text("✅ Местоположение успешно обновлено!")
            await self.show_user_menu(update, context)
            return USER_MENU
        except Exception as e:
            logger.error(f"Ошибка обновления местоположения: {e}")
            await update.message.reply_text("Произошла ошибка при обновлении местоположения.")
            return USER_MENU

    async def update_donation_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обновляет дату последней сдачи крови"""
        last_donation = update.message.text
        user = update.effective_user

        if last_donation.lower() == 'никогда':
            last_donation_date = None
        else:
            try:
                last_donation_date = datetime.strptime(last_donation, '%d.%m.%Y').date()
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
                    "Попробуйте еще раз:"
                )
                return UPDATE_DONATION_DATE

        logger.info(f"Обновление даты сдачи для пользователя {user.id}: {last_donation_date}")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users
                SET last_donation_date = %s
                WHERE telegram_id = %s
            """, (last_donation_date, user.id))

            conn.commit()
            cursor.close()
            conn.close()

            await update.message.reply_text("✅ Дата последней сдачи крови успешно обновлена!")
            await self.show_user_menu(update, context)
            return USER_MENU
        except Exception as e:
            logger.error(f"Ошибка обновления даты сдачи: {e}")
            await update.message.reply_text("Произошла ошибка при обновлении даты сдачи.")
            return USER_MENU

    async def create_donation_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание запроса на сдачу крови"""
        logger.info("Начинаем создание запроса крови")
        keyboard = [
            [InlineKeyboardButton("A+", callback_data="request_A+"),
             InlineKeyboardButton("A-", callback_data="request_A-")],
            [InlineKeyboardButton("B+", callback_data="request_B+"),
             InlineKeyboardButton("B-", callback_data="request_B-")],
            [InlineKeyboardButton("AB+", callback_data="request_AB+"),
             InlineKeyboardButton("AB-", callback_data="request_AB-")],
            [InlineKeyboardButton("O+", callback_data="request_O+"),
             InlineKeyboardButton("O-", callback_data="request_O-")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            "🩸 Создание запроса на сдачу крови\n\n"
            "Выберите нужную группу крови:",
            reply_markup=reply_markup
        )

    async def handle_blood_type_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора группы крови для запроса"""
        query = update.callback_query
        await query.answer()

        logger.info(f"Получен callback_data: {query.data}")

        if query.data == "back_to_menu":
            await self.show_doctor_menu(update, context)
            return DOCTOR_MENU

        blood_type = query.data.replace('request_', '')
        context.user_data['request_blood_type'] = blood_type

        logger.info(f"Выбрана группа крови для запроса: {blood_type}")

        await query.edit_message_text(
            f"✅ Выбрана группа крови: {blood_type}\n\n"
            "Укажите город, где нужна кровь:"
        )
        return ENTERING_REQUEST_LOCATION

    async def handle_request_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода города для запроса"""
        location = update.message.text
        context.user_data['request_location'] = location

        logger.info(f"Указан город для запроса: {location}")

        await update.message.reply_text(
            "✅ Город указан!\n\n"
            "Теперь введите полный адрес медицинского учреждения:"
        )
        return ENTERING_REQUEST_ADDRESS

    async def handle_request_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода адреса учреждения"""
        address = update.message.text
        context.user_data['request_address'] = address

        logger.info(f"Указан адрес учреждения: {address}")

        await update.message.reply_text(
            "✅ Адрес учреждения сохранен!\n\n"
            "🏥 Теперь укажите название медицинского центра/больницы:"
        )
        return ENTERING_REQUEST_HOSPITAL

    async def handle_request_hospital(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода названия медицинского центра"""
        hospital_name = update.message.text
        context.user_data['request_hospital'] = hospital_name

        logger.info(f"Указано название медицинского центра: {hospital_name}")

        await update.message.reply_text(
            "✅ Название медицинского центра сохранено!\n\n"
            "📞 Укажите контактную информацию для доноров\n"
            "(телефон, email, ФИО ответственного):"
        )
        return ENTERING_REQUEST_CONTACT

    async def handle_request_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода контактной информации"""
        contact_info = update.message.text
        context.user_data['request_contact'] = contact_info

        logger.info(f"Указана контактная информация: {contact_info}")

        await update.message.reply_text(
            "✅ Контактная информация сохранена!\n\n"
            "📅 Укажите дату, когда нужна кровь (ДД.ММ.ГГГГ):"
        )
        return ENTERING_REQUEST_DATE

    async def handle_request_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода даты для запроса"""
        try:
            request_date = datetime.strptime(update.message.text, '%d.%m.%Y').date()
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
                "Попробуйте еще раз:"
            )
            return ENTERING_REQUEST_DATE

        # Сохраняем запрос в базу данных
        user = update.effective_user
        logger.info(
            f"Сохранение запроса в БД: врач {user.id}, группа {context.user_data['request_blood_type']}, "
            f"город {context.user_data['request_location']}, адрес {context.user_data['request_address']}, "
            f"медцентр {context.user_data['request_hospital']}, контакты {context.user_data['request_contact']}, "
            f"дата {request_date}")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO donation_requests (doctor_id, blood_type, location, address, hospital_name, contact_info, request_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user.id, context.user_data['request_blood_type'],
                  context.user_data['request_location'], context.user_data['request_address'],
                  context.user_data['request_hospital'], context.user_data['request_contact'], request_date))

            # Получаем ID созданного запроса
            request_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ Запрос успешно сохранен в БД с ID {request_id}")

            # Отправляем уведомления всем подходящим донорам
            await self.notify_donors(
                context.user_data['request_blood_type'],
                context.user_data['request_location'],
                context.user_data['request_address'],
                context.user_data['request_hospital'],
                context.user_data['request_contact'],
                request_date,
                request_id
            )

            await update.message.reply_text(
                f"✅ Запрос создан!\n\n"
                f"🩸 Группа крови: {context.user_data['request_blood_type']}\n"
                f"📍 Город: {context.user_data['request_location']}\n"
                f"🏥 Медцентр: {context.user_data['request_hospital']}\n"
                f"📍 Адрес: {context.user_data['request_address']}\n"
                f"📞 Контакты: {context.user_data['request_contact']}\n"
                f"📅 Дата: {request_date.strftime('%d.%m.%Y')}\n\n"
                f"Уведомления отправлены всем подходящим донорам."
            )

            await self.show_doctor_menu(update, context)
            return DOCTOR_MENU
        except Exception as e:
            logger.error(f"Ошибка сохранения запроса в БД: {e}")
            await update.message.reply_text("Произошла ошибка при создании запроса. Попробуйте позже.")
            return DOCTOR_MENU

    async def show_my_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает запросы врача"""
        user = update.effective_user
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT dr.id, dr.doctor_id, dr.blood_type, dr.location, 
                       COALESCE(dr.hospital_name, 'Не указано') as hospital_name,
                       COALESCE(dr.address, 'Адрес не указан') as address,
                       COALESCE(dr.contact_info, 'Не указано') as contact_info,
                       dr.request_date, dr.description, dr.created_at,
                       COUNT(resp.id) as response_count
                FROM donation_requests dr
                LEFT JOIN donor_responses resp ON dr.id = resp.request_id
                WHERE dr.doctor_id = %s 
                GROUP BY dr.id, dr.doctor_id, dr.blood_type, dr.location, 
                         dr.hospital_name, dr.address, dr.contact_info,
                         dr.request_date, dr.description, dr.created_at
                ORDER BY dr.created_at DESC 
                LIMIT 10
            """, (user.id,))

            requests = cursor.fetchall()

            if requests:
                text = "📋 Ваши последние запросы:\n\n"
                for i, req in enumerate(requests, 1):
                    response_text = f"📊 Откликов: {req['response_count']}"
                    
                    text += f"{i}. 🩸 {req['blood_type']} | 📍 {req['location']} | {response_text}\n"
                    text += f"🏥 {req['hospital_name']}\n"
                    text += f"📍 {req['address']}\n"
                    text += f"📞 {req['contact_info']}\n"
                    text += f"📅 {req['request_date'].strftime('%d.%m.%Y')} | 🕒 {req['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            else:
                text = "У вас пока нет созданных запросов."

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка показа запросов врача: {e}")
            await update.callback_query.edit_message_text("Произошла ошибка при загрузке запросов.")

    async def show_donor_responses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает отклики доноров на запросы врача"""
        user = update.effective_user
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT dr.blood_type, dr.hospital_name, dr.location, dr.request_date,
                       u.first_name, u.last_name, u.username, u.blood_type as donor_blood_type,
                       u.location as donor_location, resp.responded_at, dr.id as request_id
                FROM donor_responses resp
                JOIN donation_requests dr ON resp.request_id = dr.id
                JOIN users u ON resp.donor_id = u.telegram_id
                WHERE dr.doctor_id = %s
                ORDER BY resp.responded_at DESC
                LIMIT 20
            """, (user.id,))

            responses = cursor.fetchall()

            if responses:
                text = "👥 Отклики доноров на ваши запросы:\n\n"
                
                # Группируем по запросам
                requests_dict = {}
                for resp in responses:
                    req_id = resp['request_id']
                    if req_id not in requests_dict:
                        requests_dict[req_id] = {
                            'info': resp,
                            'donors': []
                        }
                    requests_dict[req_id]['donors'].append(resp)
                
                for i, (req_id, req_data) in enumerate(requests_dict.items(), 1):
                    req_info = req_data['info']
                    donors = req_data['donors']
                    
                    text += f"{i}. 🩸 {req_info['blood_type']} | 📅 {req_info['request_date'].strftime('%d.%m.%Y')}\n"
                    text += f"🏥 {req_info['hospital_name']} | 📍 {req_info['location']}\n"
                    text += f"👥 Откликнулось доноров: {len(donors)}\n\n"
                    
                    for j, donor in enumerate(donors, 1):
                        donor_name = donor['first_name']
                        if donor['last_name']:
                            donor_name += f" {donor['last_name']}"
                        
                        username = f"@{donor['username']}" if donor['username'] else "нет username"
                        
                        text += f"  {j}. {donor_name} ({username})\n"
                        text += f"     🩸 {donor['donor_blood_type']} | 📍 {donor['donor_location']}\n"
                        text += f"     🕒 {donor['responded_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    
                    if i >= 5:  # Показываем максимум 5 запросов
                        text += "...\n"
                        break
                        
            else:
                text = "Пока нет откликов на ваши запросы.\n\nКогда доноры начнут откликаться, информация появится здесь."

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка показа откликов доноров: {e}")
            await update.callback_query.edit_message_text("Произошла ошибка при загрузке откликов.")

    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает статистику для врача"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Общее количество доноров
            cursor.execute("SELECT COUNT(*) AS total_donors FROM users WHERE role = 'user' AND is_registered = TRUE")
            total_donors = cursor.fetchone()['total_donors']

            # Количество доноров по группам крови
            cursor.execute("""
                SELECT blood_type, COUNT(*) AS count 
                FROM users 
                WHERE role = 'user' AND is_registered = TRUE
                GROUP BY blood_type
                ORDER BY blood_type
            """)
            blood_type_stats = cursor.fetchall()

            # Количество доноров, которые могут сдавать кровь
            cursor.execute("""
                SELECT COUNT(*) AS can_donate_count
                FROM users
                WHERE role = 'user' 
                  AND is_registered = TRUE
                  AND (last_donation_date IS NULL OR last_donation_date <= %s)
            """, (datetime.now().date() - timedelta(days=60),))
            can_donate_count = cursor.fetchone()['can_donate_count']

            # Формируем текст статистики
            stats_text = f"📊 Статистика системы:\n\n"
            stats_text += f"👥 Всего доноров: {total_donors}\n"
            stats_text += f"🩸 Доноры, готовые сдать кровь: {can_donate_count}\n\n"
            stats_text += "📈 Распределение по группам крови:\n"

            for stat in blood_type_stats:
                stats_text += f"• {stat['blood_type']}: {stat['count']} чел.\n"

            stats_text += "\n📋 Последние 5 запросов крови:\n"

            # Последние 5 запросов с количеством откликов
            cursor.execute("""
                SELECT dr.blood_type, dr.location, 
                       COALESCE(dr.hospital_name, 'Не указано') as hospital_name,
                       COALESCE(dr.address, 'Адрес не указан') as address, 
                       dr.request_date,
                       COUNT(resp.id) as response_count
                FROM donation_requests dr
                LEFT JOIN donor_responses resp ON dr.id = resp.request_id
                GROUP BY dr.id, dr.blood_type, dr.location, dr.hospital_name, dr.address, dr.request_date, dr.created_at
                ORDER BY dr.created_at DESC 
                LIMIT 5
            """)
            recent_requests = cursor.fetchall()

            if recent_requests:
                for i, req in enumerate(recent_requests, 1):
                    stats_text += (f"\n{i}. 🩸 {req['blood_type']} | 📍 {req['location']} | 📊 {req['response_count']} откл.\n"
                                   f"🏥 {req['hospital_name']}\n"
                                   f"📍 {req['address']}\n"
                                   f"📅 {req['request_date'].strftime('%d.%m.%Y')}")
            else:
                stats_text += "\nПока нет запросов крови."

            # Добавляем общую статистику по откликам
            cursor.execute("""
                SELECT COUNT(*) as total_responses
                FROM donor_responses
            """)
            total_responses_result = cursor.fetchone()
            total_responses = total_responses_result['total_responses'] if total_responses_result else 0

            stats_text += f"\n\n📊 Общая статистика откликов: {total_responses}"

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(stats_text, reply_markup=reply_markup)

            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка показа статистики: {e}")
            await update.callback_query.edit_message_text("Произошла ошибка при загрузке статистики.")

    async def notify_donors(self, blood_type: str, location: str, address: str, hospital_name: str, contact_info: str, request_date, request_id: int):
        """Отправляет уведомления донорам"""
        logger.info(f"Отправка уведомлений донорам группы {blood_type} в {location} ({hospital_name})")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Находим всех подходящих доноров
            cursor.execute("""
                SELECT telegram_id, first_name, last_donation_date, location 
                FROM users 
                WHERE blood_type = %s AND role = 'user' AND is_registered = TRUE
            """, (blood_type,))

            donors = cursor.fetchall()
            logger.info(f"Найдено {len(donors)} доноров группы {blood_type}")

            sent_count = 0
            for donor in donors:
                # Проверяем, может ли донор сдавать кровь
                can_donate = True
                if donor['last_donation_date']:
                    days_since = (datetime.now().date() - donor['last_donation_date']).days
                    can_donate = days_since >= 60

                if can_donate:
                    message = f"""
🆘 СРОЧНО НУЖНА КРОВЬ!

🩸 Группа крови: {blood_type}
📍 Город: {location}
🏥 Медицинский центр: {hospital_name}
📍 Адрес: {address}
📅 Дата: {request_date.strftime('%d.%m.%Y')}

📞 Контактная информация:
{contact_info}

Если вы можете помочь, пожалуйста, нажмите кнопку ниже или свяжитесь с медицинским учреждением по указанным контактам.

Спасибо за вашу готовность помочь! ❤️
                    """

                    # Создаем кнопку отклика
                    keyboard = [
                        [InlineKeyboardButton("✅ Могу помочь!", callback_data=f"respond_{request_id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    try:
                        await self.application.bot.send_message(
                            chat_id=donor['telegram_id'],
                            text=message,
                            reply_markup=reply_markup
                        )
                        sent_count += 1
                        logger.info(f"Уведомление отправлено донору {donor['telegram_id']}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления донору {donor['telegram_id']}: {e}")

            logger.info(f"Отправлено {sent_count} уведомлений из {len(donors)} возможных доноров")
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")

    async def handle_donor_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка отклика донора на запрос крови"""
        query = update.callback_query
        await query.answer()
        
        # Извлекаем ID запроса из callback_data
        request_id = int(query.data.replace("respond_", ""))
        donor_id = update.effective_user.id
        
        logger.info(f"Донор {donor_id} откликается на запрос {request_id}")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Проверяем, не откликался ли донор уже на этот запрос
            cursor.execute("""
                SELECT id FROM donor_responses 
                WHERE request_id = %s AND donor_id = %s
            """, (request_id, donor_id))
            
            if cursor.fetchone():
                await query.edit_message_text(
                    "ℹ️ Вы уже откликались на этот запрос.\n\n"
                    "Спасибо за вашу готовность помочь! ❤️"
                )
                cursor.close()
                conn.close()
                return
            
            # Сохраняем отклик в базу данных
            cursor.execute("""
                INSERT INTO donor_responses (request_id, donor_id, response_type)
                VALUES (%s, %s, 'interested')
            """, (request_id, donor_id))
            
            # Получаем информацию о запросе и доноре
            cursor.execute("""
                SELECT dr.doctor_id, dr.blood_type, dr.hospital_name, dr.location, dr.request_date,
                       u.first_name, u.last_name, u.username
                FROM donation_requests dr
                JOIN users u ON dr.doctor_id = u.telegram_id
                WHERE dr.id = %s
            """, (request_id,))
            
            request_info = cursor.fetchone()
            
            # Получаем информацию о доноре
            cursor.execute("""
                SELECT first_name, last_name, username, blood_type, location
                FROM users WHERE telegram_id = %s
            """, (donor_id,))
            
            donor_info = cursor.fetchone()
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Убираем кнопку отклика и показываем подтверждение
            await query.edit_message_text(
                query.message.text + "\n\n✅ ВЫ ОТКЛИКНУЛИСЬ НА ЭТОТ ЗАПРОС!"
            )

            # Получаем полную информацию о запросе из базы данных
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT hospital_name, address, contact_info
                FROM donation_requests 
                WHERE id = %s
            """, (request_id,))
            full_request_info = cursor.fetchone()
            cursor.close()
            conn.close()
            
            # Отправляем подробную информацию о предстоящей донации
            donation_info = f"""
🎯 ЗАПЛАНИРОВАННАЯ ДОНАЦИЯ

🩸 Группа крови: {request_info['blood_type']}
📅 Дата: {request_info['request_date'].strftime('%d.%m.%Y')}

🏥 Медицинский центр: {full_request_info['hospital_name'] or 'Не указано'}
📍 Адрес: {full_request_info['address'] or 'Не указан'}

📞 Контактная информация:
{full_request_info['contact_info'] or 'Не указано'}

❗ ВАЖНО:
• Не забудьте покушать за 2-3 часа до сдачи
• Выспитесь накануне
• Возьмите с собой документы
• Приходите вовремя

Удачи! Ваш вклад спасет жизни! ❤️
            """

            # Отправляем и закрепляем сообщение
            pinned_msg = await self.application.bot.send_message(
                chat_id=donor_id,
                text=donation_info
            )
            
            try:
                await self.application.bot.pin_chat_message(
                    chat_id=donor_id,
                    message_id=pinned_msg.message_id,
                    disable_notification=True
                )
                logger.info(f"Сообщение о донации закреплено для донора {donor_id}")
            except Exception as pin_error:
                logger.error(f"Не удалось закрепить сообщение: {pin_error}")
                # В личных чатах закрепление может не работать, это нормально
            
            # Уведомляем врача о новом отклике
            if request_info and donor_info:
                await self.notify_doctor_about_response(
                    request_info['doctor_id'], 
                    request_info, 
                    donor_info,
                    request_id
                )
            
            logger.info(f"✅ Отклик донора {donor_id} на запрос {request_id} успешно сохранен")
            
        except Exception as e:
            logger.error(f"Ошибка обработки отклика донора: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при обработке отклика. Попробуйте позже."
            )

    async def notify_doctor_about_response(self, doctor_id: int, request_info, donor_info, request_id: int):
        """Уведомляет врача о новом отклике донора"""
        try:
            # Подсчитываем общее количество откликов на этот запрос
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM donor_responses WHERE request_id = %s
            """, (request_id,))
            total_responses = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            donor_name = donor_info['first_name']
            if donor_info['last_name']:
                donor_name += f" {donor_info['last_name']}"
            
            donor_username = f"@{donor_info['username']}" if donor_info['username'] else "нет username"
            
            message = f"""
🎉 НОВЫЙ ОТКЛИК ДОНОРА!

👤 Донор: {donor_name} ({donor_username})
🩸 Группа крови: {donor_info['blood_type']}
📍 Местоположение донора: {donor_info['location']}

📋 Ваш запрос:
🩸 Группа крови: {request_info['blood_type']}
🏥 {request_info['hospital_name']}
📍 {request_info['location']}
📅 {request_info['request_date'].strftime('%d.%m.%Y')}

📊 Всего откликов на этот запрос: {total_responses}

Свяжитесь с донором для координации сдачи крови.
            """
            
            await self.application.bot.send_message(
                chat_id=doctor_id,
                text=message
            )
            
            logger.info(f"Уведомление о новом отклике отправлено врачу {doctor_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления врачу: {e}")

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает справку"""
        help_text = """
❓ Справка по BloodDonorBot

👤 Для доноров:
• Регистрируйтесь с указанием группы крови и местоположения
• Получайте уведомления о необходимости сдачи крови
• Обновляйте информацию о последней сдаче крови

👨‍⚕️ Для врачей:
• Создавайте запросы на сдачу крови
• Указывайте нужную группу крови, город и адрес учреждения
• Просматривайте статистику по системе

📋 Правила сдачи крови:
• Минимальный интервал между сдачами: 60 дней
• Следуйте рекомендациям врачей
• Поддерживайте здоровый образ жизни

🔙 Для возврата в меню нажмите кнопку "Назад"
        """

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)

    def run(self):
        """Запуск бота"""
        # Создаем приложение
        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            logger.error("Токен Telegram не найден! Убедитесь, что он указан в .env файле.")
            return

        self.application = Application.builder().token(token).build()

        # Создаем ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                CHOOSING_ROLE: [CallbackQueryHandler(self.choose_role)],
                ENTERING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_password)],
                ENTERING_BLOOD_TYPE: [
                    CallbackQueryHandler(self.handle_blood_type),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_blood_type)
                ],
                ENTERING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_location)],
                ENTERING_LAST_DONATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_last_donation)],
                ENTERING_DONATION_REQUEST: [CallbackQueryHandler(self.handle_blood_type_request)],
                ENTERING_REQUEST_LOCATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_location)],
                ENTERING_REQUEST_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_address)],
                ENTERING_REQUEST_HOSPITAL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_hospital)],
                ENTERING_REQUEST_CONTACT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_contact)],
                ENTERING_REQUEST_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_date)],
                USER_MENU: [CallbackQueryHandler(self.handle_menu_callback)],
                DOCTOR_MENU: [CallbackQueryHandler(self.handle_menu_callback)],
                UPDATE_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.update_location)],
                UPDATE_DONATION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.update_donation_date)]
            },
            fallbacks=[CommandHandler('start', self.start)]
        )

        self.application.add_handler(conv_handler)

        logger.info("Бот запущен")
        # Запускаем бота
        self.application.run_polling()


if __name__ == '__main__':
    bot = BloodDonorBot()
    bot.run()