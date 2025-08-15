-- Скрипт для создания базы данных BloodDonorBot
-- Выполните этот скрипт в PostgreSQL для создания базы данных и таблиц

-- Создание базы данных
CREATE DATABASE blood_donor_bot;

-- Подключение к созданной базе данных
\c blood_donor_bot;

-- Создание таблицы пользователей
CREATE TABLE users (
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
);

-- Создание таблицы запросов на сдачу крови
CREATE TABLE donation_requests (
    id SERIAL PRIMARY KEY,
    doctor_id BIGINT NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    location VARCHAR(255) NOT NULL,
    request_date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES users(telegram_id)
);

-- Создание индексов для улучшения производительности
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_blood_type ON users(blood_type);
CREATE INDEX idx_users_location ON users(location);
CREATE INDEX idx_users_registered ON users(is_registered);

CREATE INDEX idx_donation_requests_doctor_id ON donation_requests(doctor_id);
CREATE INDEX idx_donation_requests_blood_type ON donation_requests(blood_type);
CREATE INDEX idx_donation_requests_location ON donation_requests(location);
CREATE INDEX idx_donation_requests_date ON donation_requests(request_date);

-- Создание представления для статистики
CREATE VIEW donor_statistics AS
SELECT 
    blood_type,
    COUNT(*) as total_donors,
    COUNT(CASE WHEN last_donation_date IS NULL THEN 1 END) as new_donors,
    COUNT(CASE WHEN last_donation_date IS NOT NULL THEN 1 END) as experienced_donors,
    COUNT(CASE WHEN last_donation_date < CURRENT_DATE - INTERVAL '60 days' THEN 1 END) as available_donors
FROM users 
WHERE role = 'user' AND is_registered = TRUE
GROUP BY blood_type;

-- Создание представления для активных запросов
CREATE VIEW active_requests AS
SELECT 
    dr.id,
    dr.blood_type,
    dr.location,
    dr.request_date,
    dr.created_at,
    u.first_name as doctor_name
FROM donation_requests dr
JOIN users u ON dr.doctor_id = u.telegram_id
WHERE dr.request_date >= CURRENT_DATE
ORDER BY dr.request_date ASC;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Таблица пользователей бота (доноры и врачи)';
COMMENT ON TABLE donation_requests IS 'Таблица запросов на сдачу крови от врачей';
COMMENT ON COLUMN users.telegram_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN users.role IS 'Роль пользователя: user (донор) или doctor (врач)';
COMMENT ON COLUMN users.blood_type IS 'Группа крови пользователя';
COMMENT ON COLUMN users.location IS 'Местоположение пользователя';
COMMENT ON COLUMN users.last_donation_date IS 'Дата последней сдачи крови';
COMMENT ON COLUMN donation_requests.doctor_id IS 'ID врача, создавшего запрос';
COMMENT ON COLUMN donation_requests.blood_type IS 'Требуемая группа крови';
COMMENT ON COLUMN donation_requests.location IS 'Местоположение, где нужна кровь';
COMMENT ON COLUMN donation_requests.request_date IS 'Дата, когда нужна кровь';

-- Вывод информации о созданных объектах
SELECT 'База данных blood_donor_bot успешно создана!' as status;
SELECT 'Таблицы созданы:' as tables;
SELECT '  - users' as table_name;
SELECT '  - donation_requests' as table_name;
SELECT 'Индексы созданы для оптимизации запросов' as indexes;
SELECT 'Представления созданы для статистики' as views; 