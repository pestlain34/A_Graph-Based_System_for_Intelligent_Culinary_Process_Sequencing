import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, validators, PasswordField, EmailField, DateField, SubmitField
from wtforms.validators import ValidationError, Email
from db.db import get_db


class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя',
                           [validators.Length(min=4, max=100, message="Длина должна быть в пределах [4-100]"),
                            validators.DataRequired()])
    password = PasswordField('Пароль',
                             [validators.Length(min=4, max=255, message="Длина должна быть в пределах [4-255]"),
                              validators.DataRequired(message="Заполнение поля обязательно"),
                              validators.EqualTo('confirm', message='Пароли должны совпадать')])
    confirm = PasswordField('Подтвердите пароль')
    email = EmailField('Email', [validators.Length(min=10, max=100, message="Длина должна быть в пределах [10-100]"),
                                 validators.DataRequired(message="Заполнение поля обязательно"),
                                 validators.Email(message="Формат должен быть как для почты")])
    birthday_date = DateField('Дата рождения', format='%Y-%m-%d',
                              validators=[validators.DataRequired(message="Заполнение поля обязательно")],
                              render_kw={"type": "date"})
    submit = SubmitField("Зарегистрироваться")

    def validate_email(self, field):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM user_of_app
                WHERE email = %s LIMIT 1
                """,
                (field.data,)
            )
            if cursor.fetchone():
                raise ValidationError("Пользователь с таким email уже существует")

    def validate_username(self, field):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM user_of_app
                WHERE username = %s LIMIT 1
                """,
                (field.data,)
            )
            if cursor.fetchone():
                raise ValidationError("Пользователь с таким именем уже существует")

    def validate_birthday_date(self, field):
        if field.data > datetime.date.today():
            raise ValidationError("Дата рождения не может быть в будущем")
