# app/dashboard/routes.py
from flask import render_template, flash
from flask_login import login_required, current_user
from app.dashboard import bp

@bp.route('/dashboard')
@login_required # <--- Вот он, декоратор защиты!
def index():
    """Главная страница панели управления."""
    # Просто отображаем шаблон
    return render_template('dashboard.html', title='Панель управления')

# Можно добавить сюда же маршрут профиля
@bp.route('/profile')
@login_required
def profile():
    """Страница профиля пользователя."""
    # Формы редактирования добавим позже
    return render_template('profile.html', title='Мой профиль', user=current_user)