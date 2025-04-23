# app/auth/__init__.py
from flask import Blueprint

# Создаем Blueprint с именем 'auth'
# template_folder='templates' указывает, что шаблоны для этого blueprint
# будут искаться в папке 'templates' внутри папки 'auth'
bp = Blueprint('auth', __name__, template_folder='templates')

# Импортируем маршруты в конце, чтобы избежать циклических зависимостей,
# так как routes.py будет импортировать 'bp'
from app.auth import routes