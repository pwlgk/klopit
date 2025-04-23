# app/dashboard/__init__.py
from flask import Blueprint

# Указываем папку с шаблонами для этого блюпринта
bp = Blueprint('dashboard', __name__, template_folder='templates')

from app.dashboard import routes # Важно импортировать после создания bp