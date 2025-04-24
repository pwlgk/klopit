# app/cli.py
import click
from app.models import Role
# --- ИЗМЕНЯЕМ ЭТОТ ИМПОРТ ---
# from app import db # НЕПРАВИЛЬНО
from app.extensions import db # ПРАВИЛЬНО - импортируем из extensions
# --- КОНЕЦ ИЗМЕНЕНИЙ ---

# Можно добавить эту команду в __init__.py или зарегистрировать отдельно
def register_commands(app):
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database with default roles."""
        print("Inserting default roles...")
        Role.insert_roles() # Role.insert_roles() сама использует db
        print("Roles inserted.")