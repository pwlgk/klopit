# app/main/routes.py
from flask import render_template
from app.main import bp

@bp.route('/')
@bp.route('/index')
def index():
    # Пока просто отображаем текст или базовый шаблон
    # Можно передать какие-то данные
    return render_template("index.html", title="Главная")