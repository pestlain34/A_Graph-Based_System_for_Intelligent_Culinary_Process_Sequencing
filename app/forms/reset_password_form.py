from flask_wtf import FlaskForm
from wtforms import validators, PasswordField
from wtforms.fields.simple import SubmitField


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Введите новый пароль',
                             [validators.Length(min=4, max=255, message="Длина должна быть в пределах [4-255]"),
                              validators.DataRequired(message="Заполнение поля обязательно"),
                              validators.EqualTo('confirm', message='Пароли должны совпадать')])
    confirm = PasswordField('Подтвердите пароль')
    submit = SubmitField('Сменить пароль')
