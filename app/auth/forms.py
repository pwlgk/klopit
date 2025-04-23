# app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User # Импортируем модель для проверки уникальности

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя',
                           validators=[DataRequired(message="Имя пользователя обязательно."),
                                       Length(min=3, max=20, message="Имя должно быть от 3 до 20 символов.")])
    email = StringField('Email',
                        validators=[DataRequired(message="Email обязателен."),
                                    Email(message="Некорректный формат Email.")])
    password = PasswordField('Пароль',
                             validators=[DataRequired(message="Пароль обязателен."),
                                         Length(min=6, message="Пароль должен быть не менее 6 символов.")])
    password2 = PasswordField('Повторите пароль',
                              validators=[DataRequired(message="Повторите пароль."),
                                          EqualTo('password', message="Пароли должны совпадать.")])
    submit = SubmitField('Зарегистрироваться')

    # Кастомные валидаторы для проверки уникальности
    def validate_username(self, username):
        """Проверяет, не занято ли имя пользователя."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

    def validate_email(self, email):
        """Проверяет, не занят ли email."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован. Пожалуйста, используйте другой.')

# Форма Логина будет добавлена позже
# class LoginForm(FlaskForm):
#     ...