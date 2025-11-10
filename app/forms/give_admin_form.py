from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class Give_Admin(FlaskForm):
    submit = SubmitField('Дать права админа')
