# app/dashboard/routes.py
from flask import render_template, flash, abort, redirect, url_for, request
from flask_login import login_required, current_user, logout_user # Добавили logout_user
from app.dashboard import bp
from app.extensions import db # Импорт db
from app.utils.decorators import admin_required # Декоратор админа
from app.models import User, Notification,  Role # Модели
from app.dashboard.forms import ProfileEditForm, ChangePasswordForm, AdminEditUserForm  # Формы
from datetime import datetime # Для отметки времени прочтения уведомлений
import traceback # Для отладки

# --- Главная страница Панели управления ---
@bp.route('/dashboard')
@login_required
def index():
    """Главная страница панели управления."""
    return render_template('dashboard.html', title='Панель управления')

# --- Просмотр Профиля ---
@bp.route('/profile')
@login_required
def profile():
    """Страница профиля пользователя."""
    return render_template('profile.html', title='Мой профиль', user=current_user)

# --- Редактирование Профиля ---
@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Редактирование имени пользователя и email."""
    # Передаем оригинальные данные в конструктор формы для валидации уникальности
    form = ProfileEditForm(original_username=current_user.username,
                           original_email=current_user.email)

    if form.validate_on_submit():
        try:
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Ваш профиль успешно обновлен.', 'success')
            return redirect(url_for('dashboard.profile')) # Возвращаемся на страницу профиля
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении профиля: {e}', 'danger')
            print(f"Profile edit error: {e}")
            traceback.print_exc()
    elif request.method == 'GET':
        # Заполняем форму текущими данными пользователя для GET запроса
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('edit_profile.html', title='Редактирование профиля', form=form)

# --- Смена Пароля ---
@bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Смена пароля пользователя (требуется текущий пароль)."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        # Проверяем текущий пароль
        if current_user.check_password(form.current_password.data):
            try:
                current_user.set_password(form.new_password.data)
                db.session.commit()
                flash('Пароль успешно изменен. Пожалуйста, войдите снова.', 'success')
                # Выходим из системы после смены пароля для безопасности
                logout_user()
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при смене пароля: {e}', 'danger')
                print(f"Change password error: {e}")
                traceback.print_exc()
        else:
            flash('Неверный текущий пароль.', 'danger')
    return render_template('change_password.html', title='Смена пароля', form=form)

# --- Настройки Аккаунта ---
@bp.route('/settings')
@login_required
def settings():
    """Страница настроек аккаунта."""
    return render_template('settings.html', title='Настройки')

# --- Список Уведомлений ---
@bp.route('/notifications')
@login_required
def notifications():
    """Отображает уведомления пользователя и помечает их как прочитанные."""
    # Получаем недавние уведомления пользователя, сортируем по убыванию даты
    # Можно добавить пагинацию для большого количества уведомлений
    user_notifications = current_user.notifications.order_by(Notification.timestamp.desc()).all()

    # Помечаем все непрочитанные как прочитанные
    updated = False
    try:
        # Эффективнее сделать одним update, если записей много, но так проще для примера
        for notification in current_user.notifications.filter_by(is_read=False):
             notification.is_read = True
             updated = True
        if updated:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notifications as read for user {current_user.id}: {e}")
        traceback.print_exc()
        # Можно добавить flash сообщение об ошибке

    return render_template('notifications.html', title='Уведомления',
                           notifications=user_notifications)


# --- Раздел Администрирования (Только для Админов) ---
@bp.route('/admin/users')
@login_required
@admin_required # Применяем декоратор прав администратора
def list_users():
    """Отображает список всех пользователей (только для админов)."""
    page = request.args.get('page', 1, type=int)
    per_page = 20 # Количество пользователей на странице
    # Получаем пагинированный список пользователей
    pagination = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    return render_template('admin/user_list.html', title='Список пользователей',
                           users=users, pagination=pagination)

@bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Редактирование пользователя администратором."""
    user = User.query.get_or_404(user_id)
    # Передаем редактируемого пользователя в форму для валидации
    form = AdminEditUserForm(user_to_edit=user)

    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data # QuerySelectField возвращает объект Role
            user.is_active = form.is_active.data
            db.session.commit()
            flash(f'Данные пользователя {user.username} обновлены.', 'success')
            return redirect(url_for('dashboard.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении пользователя: {e}', 'danger')
            print(f"Admin user edit error: {e}")
            traceback.print_exc()
    elif request.method == 'GET':
        # Предзаполняем форму данными пользователя
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role # Устанавливаем текущую роль
        form.is_active.data = user.is_active

    return render_template('admin/edit_user.html', title=f'Редактирование: {user.username}', form=form, user=user)

@bp.route('/admin/users/<int:user_id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Переключает статус активности пользователя."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Вы не можете деактивировать свой собственный аккаунт.', 'warning')
        return redirect(url_for('dashboard.list_users'))
    try:
        user.is_active = not user.is_active
        db.session.commit()
        status = "активирован" if user.is_active else "деактивирован"
        flash(f'Пользователь {user.username} был {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при изменении статуса пользователя: {e}', 'danger')
        print(f"Toggle user active error: {e}")
        traceback.print_exc()
    return redirect(url_for('dashboard.list_users'))