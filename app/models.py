# app/models.py
from datetime import datetime
from flask_login import UserMixin # Импортируем UserMixin
from app.extensions import db, bcrypt # Импортируем db и bcrypt из extensions

# Модель пользователя
class User(UserMixin, db.Model): # Наследуем UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True) # Для возможности деактивации

    # Отношения (добавятся позже)
    # projects = db.relationship('Project', backref='owner', lazy='dynamic')
    # tasks_assigned = db.relationship('Task', backref='assignee', lazy='dynamic')

    def set_password(self, password):
        """Генерирует хеш пароля и сохраняет его."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Проверяет введенный пароль с сохраненным хешем."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Другие модели (Project, Task, etc.) будут добавлены здесь позже