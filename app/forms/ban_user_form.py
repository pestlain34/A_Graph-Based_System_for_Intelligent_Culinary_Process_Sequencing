from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class Ban_User_Form(FlaskForm):
    submit = SubmitField('Забанить')
