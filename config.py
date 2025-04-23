# config.py
import os

class Config:
    # Генерируйте свой собственный сложный ключ!
    # Можно использовать: import secrets; secrets.token_hex(16)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'KKBKHBKKKBKHBHBKBBKHBBB_RANDOMKEY' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Отключаем ненужные уведомления SQLAlchemy
    # URI базы данных будет добавлен позже