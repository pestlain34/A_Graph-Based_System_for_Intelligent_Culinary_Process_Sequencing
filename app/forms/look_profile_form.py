from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class Look_User(FlaskForm):
    submit = SubmitField('Просмотреть пользователя')
