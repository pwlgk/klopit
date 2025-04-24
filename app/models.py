# app/models.py
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, bcrypt
import enum # Для статусов и приоритетов
import uuid # Для генерации уникальных имен файлов
import os
from werkzeug.utils import secure_filename # Для безопасных имен файлов
from flask import current_app # Для доступа к config


# --- Enum для статусов и приоритетов ---
class TaskStatus(enum.Enum):
    TODO = 'К выполнению'
    IN_PROGRESS = 'В работе'
    DONE = 'Выполнено'
    ARCHIVED = 'В архиве' # Опционально

class TaskPriority(enum.Enum):
    LOW = 'Низкий'
    MEDIUM = 'Средний'
    HIGH = 'Высокий'

# --- Таблица связей User <-> Project ---
# Определяем таблицу вне классов моделей
project_members = db.Table('project_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), primary_key=True)
    # ondelete='CASCADE': если удаляется пользователь или проект, запись из этой таблицы тоже удаляется
)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False) # Имя роли ('Admin', 'User')
    # Опционально: разрешения, связанные с ролью (для более сложной системы)
    # permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic') # Связь с пользователями

    def __repr__(self):
        return f'<Role {self.name}>'

    # --- Статический метод для вставки ролей при инициализации ---
    @staticmethod
    def insert_roles():
        roles = ['User', 'Admin']
        for r_name in roles:
            role = Role.query.filter_by(name=r_name).first()
            if role is None: # Если роли еще нет
                role = Role(name=r_name)
                db.session.add(role)
        db.session.commit() # Сохраняем добавленные роли


# --- Модель User ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # --- Внешний ключ и связь с Role ---
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    # Конструктор для установки роли по умолчанию
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None: # Если роль не была задана явно
            # Ищем роль 'User'
            default_role = Role.query.filter_by(name='User').first()
            if default_role:
                self.role = default_role
            else:
                # На случай, если роль 'User' еще не создана (хотя insert_roles должна помочь)
                # Можно либо создать ее здесь, либо вызвать ошибку, либо оставить None
                print("WARNING: Default role 'User' not found for new user.")
                pass # Оставляем None или можно назначить Admin, если это первый пользователь

    # --- Остальные связи ---
    projects_owned = db.relationship('Project', backref='owner', lazy='dynamic', foreign_keys='Project.owner_id')
    # --- Новая связь: Проекты, в которых пользователь УЧАСТВУЕТ ---
    # secondary=project_members: указывает на таблицу связей
    # back_populates='members': имя атрибута в модели Project для обратной связи
    # lazy='dynamic': для возможности фильтрации/пагинации
    projects_member_of = db.relationship('Project', secondary=project_members,
                                         back_populates='members', lazy='dynamic')
    tasks_assigned = db.relationship('Task', backref='assignee', lazy='dynamic', foreign_keys='Task.assignee_id')
    tasks_created = db.relationship('Task', backref='creator', lazy='dynamic', foreign_keys='Task.creator_id')
    uploaded_files = db.relationship('File', backref='uploader', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic',
                                    foreign_keys='Notification.user_id')

    # ... (методы set_password, check_password, __repr__) ...
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f'<User {self.username} ({self.role.name if self.role else "No Role"})>'

    # --- Метод для проверки прав администратора ---
    def is_admin(self):
        return self.role is not None and self.role.name == 'Admin'
    
    def is_member_of(self, project):
        return self.projects_member_of.filter(project_members.c.project_id == project.id).count() > 0

    # --- Новый метод: проверка, имеет ли доступ к проекту (владелец ИЛИ участник) ---
    def can_access_project(self, project):
         return self.id == project.owner_id or self.is_member_of(project)

    # --- Метод для получения непрочитанных уведомлений ---
    def new_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()

# --- Модель Project ---
class Project(db.Model):
    # ... (поля id, name, description, created_at, owner_id) ...
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), index=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    

    # --- Связи ---
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Task.project_id')
    files = db.relationship('File', backref='project', lazy='dynamic', cascade='all, delete-orphan') # backref из File
    # --- Новая связь: Участники проекта ---
    # back_populates='projects_member_of': имя атрибута в модели User
    members = db.relationship('User', secondary=project_members,
                              back_populates='projects_member_of', lazy='dynamic')

    # ... (__repr__) ...
    def __repr__(self):
        return f'<Project {self.name}>'

# --- Модель Task ---
class Task(db.Model):
    # ... (поля id, title, description, status, priority, created_at, due_date, project_id, assignee_id, creator_id) ...
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # --- Связи ---
    files = db.relationship('File', backref='task', lazy='dynamic', cascade='all, delete-orphan') # backref из File
    # --- Новая связь с комментариями ---
    # cascade='all, delete-orphan': Комментарии удаляются вместе с задачей
    comments = db.relationship('Comment', backref='task', lazy='dynamic', cascade='all, delete-orphan')

    # ... (__repr__) ...
    def __repr__(self):
        return f'<Task {self.title}>'

# --- Модель File ---
class File(db.Model):
    # ... (поля id, storage_filename, original_filename, uploaded_at, user_id, task_id, project_id) ...
    id = db.Column(db.Integer, primary_key=True)
    storage_filename = db.Column(db.String(300), unique=True, nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=True)

    # ... (методы generate_storage_filename, filepath, is_allowed, __repr__) ...
    @staticmethod
    def generate_storage_filename(original_filename):
        _, ext = os.path.splitext(original_filename)
        safe_basename = secure_filename(os.path.splitext(original_filename)[0])
        unique_id = uuid.uuid4().hex
        max_base_len = 200
        safe_basename = safe_basename[:max_base_len]
        return f"{safe_basename}_{unique_id}{ext}"
    @property
    def filepath(self):
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.storage_filename)
    @staticmethod
    def is_allowed(filename):
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS')
        if not allowed_extensions: return True
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    def __repr__(self):
        return f'<File {self.original_filename} (Stored: {self.storage_filename})>'


# --- Новая Модель Комментария ---
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False) # Текст комментария
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # Внешний ключ к автору комментария
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Внешний ключ к задаче, к которой относится комментарий
    # ondelete='CASCADE': комментарий удаляется из БД при удалении задачи
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)

    # Связи (backrefs созданы в User и Task)

    def __repr__(self):
        return f'<Comment {self.id} by User {self.user_id} on Task {self.task_id}>'
    


    # --- Модель Уведомления ---
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ID пользователя, для которого предназначено уведомление
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    # Текст уведомления
    message = db.Column(db.Text, nullable=False)
    # Время создания
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # Флаг: прочитано ли уведомление
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    # Ссылка на связанный объект (например, на задачу или проект)
    related_url = db.Column(db.String(500), nullable=True)

    # Связь (backref='recipient' создан в User)

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'