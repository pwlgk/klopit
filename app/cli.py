# app/cli.py
import click
from flask.cli import with_appcontext # Помогает с контекстом приложения
from app.models import User, Role    # Импортируем модели
from app.extensions import db        # Импортируем db из extensions

# Эта функция будет регистрировать все наши команды
def register_commands(app):

    # --- Команда для инициализации ролей ---
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database with default roles (User, Admin)."""
        click.echo("Проверка и вставка стандартных ролей...")
        try:
            Role.insert_roles() # Вызываем статический метод из модели Role
            click.echo("Стандартные роли успешно добавлены или уже существуют.")
        except Exception as e:
             # Выводим ошибку, если что-то пошло не так с БД
             click.echo(f"Ошибка при вставке ролей: {e}")
             click.echo("Убедитесь, что база данных существует и миграции применены ('flask db upgrade').")

    @app.cli.command('assign-admin')
    @click.argument('email') # Принимаем email как обязательный аргумент командной строки
    def assign_admin_role(email):
        """Assigns the Admin role to a user specified by email."""
        # Ищем пользователя по email (регистронезависимо)
        user = User.query.filter(User.email.ilike(email)).first()

        if not user:
            click.echo(f"Ошибка: Пользователь с email '{email}' не найден.")
            return # Завершаем команду

        # Ищем роль Admin
        admin_role = Role.query.filter_by(name='Admin').first()

        if not admin_role:
            click.echo("Ошибка: Роль 'Admin' не найдена в базе данных.")
            click.echo("Сначала выполните команду 'flask init-db'.")
            return # Завершаем команду

        # Проверяем, не является ли пользователь уже админом
        if user.role == admin_role:
            click.echo(f"Пользователь '{user.username}' (Email: {email}) уже является администратором.")
            return # Завершаем команду

        # Назначаем роль и сохраняем
        try:
            user.role = admin_role
            db.session.commit()
            click.echo(f"Роль 'Admin' успешно назначена пользователю '{user.username}' (Email: {email}).")
        except Exception as e:
            db.session.rollback() # Откатываем транзакцию в случае ошибки
            click.echo(f"Ошибка при назначении роли: {e}")
            click.echo("Изменения не были сохранены.")
