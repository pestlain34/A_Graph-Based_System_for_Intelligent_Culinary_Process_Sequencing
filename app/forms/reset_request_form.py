from flask_wtf import FlaskForm
from wtforms import EmailField, validators, SubmitField


class RequestResetForm(FlaskForm):
    email = EmailField('Email', [validators.Length(min=10, max=100, message="Длина должна быть в пределах [10-100]"),
                                 validators.DataRequired(message="Заполнение поля обязательно"),
                                 validators.Email(message="Формат должен быть как для почты")])
    submit = SubmitField('Отправить ссылку для восстановления пароля')
