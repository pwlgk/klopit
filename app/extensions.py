# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
# from flask_mail import Mail # Раскомментируем позже

db = SQLAlchemy()
migrate = Migrate()
# Создаем экземпляр LoginManager
login_manager = LoginManager()
# Указываем Flask-Login, какая view отвечает за логин.
# Flask-Login будет перенаправлять сюда пользователей,
# которые пытаются получить доступ к @login_required страницам.
# 'auth.login' - 'auth' это имя Blueprint, 'login' - имя функции view.
login_manager.login_view = 'auth.login'
# Сообщение, которое будет показано пользователю при перенаправлении на логин
login_manager.login_message = 'Пожалуйста, войдите в систему, чтобы получить доступ к этой странице.'
login_manager.login_message_category = 'info' # Категория для flash сообщения

csrf = CSRFProtect()
bcrypt = Bcrypt()
# mail = Mail() # Раскомментируем позже