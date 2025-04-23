# app/__init__.py
from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений будет здесь (позже)
    # db.init_app(app)
    # migrate.init_app(app, db)
    # login.init_app(app)
    # mail.init_app(app)
    # ... и т.д.

    # Регистрация Blueprints будет здесь (позже)
    # from app.auth import bp as auth_bp
    # app.register_blueprint(auth_bp, url_prefix='/auth')
    # ... и т.д.

    # Простой тестовый маршрут
    @app.route('/')
    @app.route('/index')
    def index():
        # Пока просто текст, позже будем использовать render_template
        return "Привет, KLOPIT! (Этап 0)"

    # Добавим маршрут для проверки base.html
    @app.route('/test_base')
    def test_base():
        from flask import render_template
        # Убедимся, что шаблон base.html существует и рендерится
        return render_template('base.html', title='Тест Базы')


    return app