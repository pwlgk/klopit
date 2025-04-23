# config.py
import os
basedir = os.path.abspath(os.path.dirname(__file__)) # Получаем абсолютный путь к папке проекта

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-fallback-secret-key-here' # ЗАМЕНИТЕ ЭТО!

    # --- Настройки Базы Данных ---
    # Указываем путь к файлу БД SQLite внутри папки проекта
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Отключаем ненужные уведомления SQLAlchemy

    # --- Настройки Почты (понадобятся позже для сброса пароля) ---
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMINS = ['your-email@example.com'] # Адрес для получения ошибок