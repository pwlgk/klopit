# app/__init__.py
from flask import Flask, render_template # Добавили render_template
from config import Config
from .extensions import db, migrate, login_manager, csrf, bcrypt # mail # Добавили импорты

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app) # Инициализация CSRF защиты
    bcrypt.init_app(app) # Инициализация Bcrypt
    # mail.init_app(app) # Позже

    # Регистрация Blueprints
    # --- Модуль Аутентификации ---
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # --- Модуль Главной страницы (если нужен отдельный) ---
    # Пример: создадим простой Blueprint для главной страницы
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)


    # --- Регистрация обработчика пользователя для Flask-Login ---
    # Flask-Login должен знать, как загрузить пользователя по ID
    from app.models import User # Убедитесь, что модели импортируются ПОСЛЕ инициализации db
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Удаляем старые тестовые маршруты, так как / будет обрабатываться main_bp
    # @app.route('/')
    # @app.route('/index') ...

    @app.route('/test_base')
    def test_base():
        return render_template('base.html', title='Тест Базы')

    return app

# Важно: Импортируем модели *после* создания фабрики и инициализации db,
# чтобы избежать циклических импортов, если модели импортируют db.
# Хотя в нашем случае модели будут импортировать db из extensions.
# Правильнее импортировать модели там, где они нужны (например, в user_loader).
# from app import models # Можно пока убрать отсюда