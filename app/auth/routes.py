# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required # Добавили login_required
from urllib.parse import urlparse # Для безопасного редиректа (используем встроенный модуль)
from app.extensions import db
from app.auth import bp
from app.auth.forms import RegistrationForm, LoginForm # Импортируем LoginForm
from app.models import User


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
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже вошел, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Ищем пользователя по email
        user = User.query.filter_by(email=form.email.data).first()

        # Проверяем, найден ли пользователь и совпадает ли пароль
        if user is None or not user.check_password(form.password.data):
            flash('Неверный email или пароль.', 'danger') # Сообщение об ошибке
            return redirect(url_for('auth.login')) # Перезагружаем страницу входа

        # Если все верно, логиним пользователя
        # form.remember_me.data содержит True/False из чекбокса
        login_user(user, remember=form.remember_me.data)
        flash(f'Добро пожаловать, {user.username}!', 'success')

        # --- Безопасное перенаправление после входа ---
        # Если пользователь пытался зайти на защищенную страницу,
        # Flask-Login сохранит ее URL в параметре 'next' строки запроса.
        next_page = request.args.get('next')
        # Проверяем, что next_page существует и является относительным URL
        # (защита от Open Redirect Attack)
        if not next_page or urlparse(next_page).netloc != '':            
            next_page = url_for('main.index') # Если нет 'next' или он небезопасный, идем на главную

        return redirect(next_page) # Перенаправляем куда нужно

    # Отображаем шаблон с формой входа (для GET запроса или если форма невалидна)
    return render_template('login.html', title='Вход', form=form)

@bp.route('/logout')
@login_required # Выйти может только залогиненный пользователь
def logout():
    logout_user() # Функция Flask-Login для удаления сессии пользователя
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('main.index')) # Перенаправляем на главную