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
    ENTERING_REQUEST_LOCATION, ENTERING_REQUEST_ADDRESS, ENTERING_REQUEST_DATE, \
    UPDATE_LOCATION, UPDATE_DONATION_DATE = range(13)

# Мастер-пароль для врачей
MASTER_PASSWORD = "doctor2024"


class BloodDonorBot:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'blood_donor_bot'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
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
            await query.edit_message_text(
                "👤 Отлично! Вы выбрали роль донора.\n\n"
                "Для регистрации вам нужно будет указать:\n"
                "• Группу крови\n"
                "• Местоположение\n"
                "• Дату последней сдачи крови\n\n"
                "Придумайте пароль для вашего аккаунта:"
            )
            return ENTERING_PASSWORD
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
        """Обработка ввода группы крови"""
        blood_type = update.message.text.upper()
        valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

        if blood_type not in valid_types:
            await update.message.reply_text(
                "❌ Неверный формат группы крови. Используйте формат: A+, B-, AB+, O- и т.д.\n"
                "Попробуйте еще раз:"
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
        elif query.data == "update_donation":
            await query.edit_message_text(
                "Введите дату последней сдачи крови в формате ДД.ММ.ГГГГ\n"
                "(или напишите 'никогда', если вы еще не сдавали кровь):"
            )
            return UPDATE_DONATION_DATE
        elif query.data == "update_location":
            await query.edit_message_text("Введите новое местоположение (город):")
            return UPDATE_LOCATION
        elif query.data == "create_request":
            logger.info("Создание запроса крови")
            await self.create_donation_request(update, context)
            return ENTERING_DONATION_REQUEST
        elif query.data == "my_requests":
            await self.show_my_requests(update, context)
            return DOCTOR_MENU
        elif query.data == "statistics":
            await self.show_statistics(update, context)
            return DOCTOR_MENU
        elif query.data == "help":
            await self.show_help(update, context)
            return DOCTOR_MENU if self.is_doctor(update.effective_user.id) else USER_MENU
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
            [InlineKeyboardButton("A+", callback_data="blood_A+"),
             InlineKeyboardButton("A-", callback_data="blood_A-")],
            [InlineKeyboardButton("B+", callback_data="blood_B+"),
             InlineKeyboardButton("B-", callback_data="blood_B-")],
            [InlineKeyboardButton("AB+", callback_data="blood_AB+"),
             InlineKeyboardButton("AB-", callback_data="blood_AB-")],
            [InlineKeyboardButton("O+", callback_data="blood_O+"),
             InlineKeyboardButton("O-", callback_data="blood_O-")],
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

        blood_type = query.data.replace('blood_', '')
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
            "Укажите дату, когда нужна кровь (ДД.ММ.ГГГГ):"
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
            f"дата {request_date}")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO donation_requests (doctor_id, blood_type, location, address, request_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (user.id, context.user_data['request_blood_type'],
                  context.user_data['request_location'], context.user_data['request_address'], request_date))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info("✅ Запрос успешно сохранен в БД")

            # Отправляем уведомления всем подходящим донорам
            await self.notify_donors(
                context.user_data['request_blood_type'],
                context.user_data['request_location'],
                context.user_data['request_address'],
                request_date
            )

            await update.message.reply_text(
                f"✅ Запрос создан!\n\n"
                f"🩸 Группа крови: {context.user_data['request_blood_type']}\n"
                f"📍 Город: {context.user_data['request_location']}\n"
                f"🏥 Адрес: {context.user_data['request_address']}\n"
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
                SELECT * FROM donation_requests 
                WHERE doctor_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (user.id,))

            requests = cursor.fetchall()

            if requests:
                text = "📋 Ваши последние запросы:\n\n"
                for req in requests:
                    text += f"🩸 {req['blood_type']} | 📍 {req['location']} | 🏥 {req['address']}\n"
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

            # Последние 5 запросов
            cursor.execute("""
                SELECT blood_type, location, address, request_date 
                FROM donation_requests 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            recent_requests = cursor.fetchall()

            if recent_requests:
                for i, req in enumerate(recent_requests, 1):
                    stats_text += (f"\n{i}. 🩸 {req['blood_type']} | 📍 {req['location']}\n"
                                   f"🏥 Адрес: {req['address']}\n"
                                   f"📅 Дата: {req['request_date'].strftime('%d.%m.%Y')}")
            else:
                stats_text += "\nПока нет запросов крови."

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(stats_text, reply_markup=reply_markup)

            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка показа статистики: {e}")
            await update.callback_query.edit_message_text("Произошла ошибка при загрузке статистики.")

    async def notify_donors(self, blood_type: str, location: str, address: str, request_date):
        """Отправляет уведомления донорам"""
        logger.info(f"Отправка уведомлений донорам группы {blood_type} в {location} по адресу {address}")

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
🏥 Адрес учреждения: {address}
📅 Дата: {request_date.strftime('%d.%m.%Y')}

Если вы можете помочь, пожалуйста, свяжитесь с медицинским учреждением.

Спасибо за вашу готовность помочь! ❤️
                    """

                    try:
                        await self.application.bot.send_message(
                            chat_id=donor['telegram_id'],
                            text=message
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
                ENTERING_BLOOD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_blood_type)],
                ENTERING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_location)],
                ENTERING_LAST_DONATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_last_donation)],
                ENTERING_DONATION_REQUEST: [CallbackQueryHandler(self.handle_blood_type_request)],
                ENTERING_REQUEST_LOCATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_location)],
                ENTERING_REQUEST_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_request_address)],
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