# app/dashboard/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, BooleanField # Добавили SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo
from wtforms_sqlalchemy.fields import QuerySelectField # Для выбора роли
from app.models import User, Role # Импортируем Role

class ProfileEditForm(FlaskForm):
    # ... (форма редактирования своего профиля - без изменений) ...
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Сохранить изменения')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user: raise ValidationError('Это имя пользователя уже занято.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user: raise ValidationError('Этот email уже используется.')

class ChangePasswordForm(FlaskForm):
    # ... (форма смены своего пароля - без изменений) ...
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField(
        'Повторите новый пароль',
        validators=[DataRequired(), EqualTo('new_password', message='Пароли должны совпадать.')]
    )
    submit = SubmitField('Сменить пароль')

# --- Новая форма для редактирования пользователя админом ---
def get_roles():
    # Фабрика для QuerySelectField, возвращает все роли
    return Role.query.order_by(Role.name)

class AdminEditUserForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Выбор роли из существующих
    role = QuerySelectField('Роль', query_factory=get_roles, get_label='name', allow_blank=False, validators=[DataRequired()])
    is_active = BooleanField('Активен') # Чекбокс для статуса
    submit = SubmitField('Сохранить пользователя')

    def __init__(self, user_to_edit, *args, **kwargs):
        super(AdminEditUserForm, self).__init__(*args, **kwargs)
        self.user_to_edit = user_to_edit # Сохраняем пользователя для валидации

    def validate_username(self, username):
        # Проверяем уникальность, только если имя изменилось
        if username.data != self.user_to_edit.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Это имя пользователя уже занято.')

    def validate_email(self, email):
        # Проверяем уникальность, только если email изменился
        if email.data != self.user_to_edit.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Этот email уже используется.')