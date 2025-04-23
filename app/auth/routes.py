# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user # Пока не используем, но импортируем для будущего
from app import db # Импортируем db из главного __init__ (или лучше из extensions?) - лучше из extensions
# from app.extensions import db # Правильнее так
from app.auth import bp # Импортируем наш Blueprint
from app.auth.forms import RegistrationForm # Импортируем форму
from app.models import User # Импортируем модель User

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Если пользователь уже вошел в систему, перенаправляем его
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Перенаправляем на главную

    form = RegistrationForm()
    if form.validate_on_submit():
        # Если форма валидна при отправке (POST запрос)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data) # Хешируем пароль
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы успешно зарегистрированы!', 'success')
        # Перенаправляем на страницу входа после успешной регистрации
        # return redirect(url_for('auth.login')) # Сделаем позже
        return redirect(url_for('main.index')) # Пока на главную

    # Если GET запрос или форма невалидна, просто отображаем шаблон с формой
    return render_template('register.html', title='Регистрация', form=form)

# Маршрут для логина (пока заглушка)
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Логика входа будет здесь
    return "Страница входа (будет реализована позже)"

# Маршрут для выхода (пока заглушка)
@bp.route('/logout')
def logout():
    # Логика выхода будет здесь
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))