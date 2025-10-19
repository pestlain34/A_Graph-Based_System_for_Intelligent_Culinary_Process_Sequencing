from flask_wtf import FlaskForm
from wtforms import StringField, validators, PasswordField, SubmitField, BooleanField


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', [validators.DataRequired(message = "Введите имя пользователя")])
    password = PasswordField('Пароль' , [validators.DataRequired(message = "Введите пароль")])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
