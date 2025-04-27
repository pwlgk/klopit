# app/projects/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField, EmailField
from wtforms.validators import DataRequired, Length, Optional, Email
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import TaskStatus, TaskPriority, User

# --- Функция для получения списка пользователей для выбора ---
# Эта функция будет передана в QuerySelectField
def get_users():
    # Возвращаем Query объект, QuerySelectField сам выполнит .all()
    # Можно добавить фильтрацию, например, только активных пользователей
    return User.query.order_by(User.username)

class ProjectForm(FlaskForm):
    name = StringField('Название проекта',
                       validators=[DataRequired(message="Название проекта обязательно."),
                                   Length(min=3, max=150)])
    description = TextAreaField('Описание проекта (опционально)',
                                validators=[Length(max=500)])
    submit = SubmitField('Сохранить проект')

class AddMemberForm(FlaskForm):
    email = EmailField('Email пользователя',
                       validators=[DataRequired(message="Email обязателен."),
                                   Email(message="Некорректный формат Email.")])
    submit = SubmitField('Добавить участника')

# ---  Форма Задачи ---
class TaskForm(FlaskForm):
    title = StringField('Название задачи',
                        validators=[DataRequired(message="Название обязательно."),
                                    Length(min=3, max=200)])
    description = TextAreaField('Описание (опционально)',
                                validators=[Optional(), Length(max=1000)])
    # Работаем с именами Enum (строками)
    status = SelectField('Статус',
                         choices=[(stat.name, stat.value) for stat in TaskStatus],
                         validators=[DataRequired()])
    priority = SelectField('Приоритет',
                           choices=[(prio.name, prio.value) for prio in TaskPriority],
                           validators=[DataRequired()])

    assignee_id = QuerySelectField('Исполнитель (опционально)',
                                   query_factory=get_users,
                                   allow_blank=True,
                                   get_label='username',
                                   validators=[Optional()])
    due_date = DateField('Срок выполнения (опционально)',
                         format='%Y-%m-%d',
                         validators=[Optional()])
    submit = SubmitField('Сохранить задачу')

class CommentForm(FlaskForm):
    body = TextAreaField('Ваш комментарий',
                         validators=[DataRequired(message="Комментарий не может быть пустым."),
                                     Length(min=1, max=1000)])
    submit = SubmitField('Отправить')