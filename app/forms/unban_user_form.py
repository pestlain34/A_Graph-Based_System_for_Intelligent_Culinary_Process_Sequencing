from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class Unban_User_Form(FlaskForm):
    submit = SubmitField('Разбанить')
