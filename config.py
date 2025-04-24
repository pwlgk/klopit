# config.py
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Gvhvhhgfggcchc' # ЗАМЕНИТЕ ЭТО!
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Настройки Загрузки Файлов ---
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    # Максимальный размер файла (например, 16 МБ)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    # Расширения, которые разрешено загружать (пример)
    # Оставьте пустым или None, чтобы разрешить любые файлы (менее безопасно)
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}


    # --- Настройки Почты (понадобятся позже для сброса пароля) ---
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMINS = ['your-email@example.com'] # Адрес для получения ошибок