# app/__init__.py
from flask import Flask, current_app, render_template
from app import cli
from config import Config
from .extensions import db, migrate, login_manager, csrf, bcrypt # mail
from datetime import date
# --- Импортируем классы Enum ---
from app.models import User, TaskStatus, TaskPriority, Comment
from flask_login import current_user

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

   

    # Инициализация расширений...
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)

    # Регистрация Blueprints...
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    from app.projects import bp as projects_bp
    app.register_blueprint(projects_bp, url_prefix='/projects')
    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports') 
    from app.files import bp as files_bp
    app.register_blueprint(files_bp, url_prefix='/files') 

    # --- Регистрация CLI команд ---
    cli.register_commands(app)

    # Регистрация обработчика пользователя для Flask-Login...
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Контекстный процессор ---
    @app.context_processor
    def inject_context():
         # --- Получаем кол-во непрочитанных уведомлений ---
        unread_notifications_count = 0
        if current_user.is_authenticated: # Только для аутентифицированных
            unread_notifications_count = current_user.new_notifications_count()
        # Рассчитываем максимальный размер в МБ один раз здесь
        max_size_mb = 0
        max_length = current_app.config.get('MAX_CONTENT_LENGTH')
        if max_length:
            max_size_mb = round(max_length / 1024 / 1024)

        # Передаем классы Enum, дату и нужные параметры конфига
        return dict(
            
            today_date=date.today(),
            TaskStatus=TaskStatus,
            TaskPriority=TaskPriority,
             unread_notifications_count=unread_notifications_count,
            Comment=Comment, 
            # Передаем конкретные значения из конфига
            MAX_UPLOAD_SIZE_MB=max_size_mb,
            ALLOWED_EXTENSIONS_CONFIG=current_app.config.get('ALLOWED_EXTENSIONS')
        )

    return app

