from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class PublicateForm(FlaskForm):
    submit = SubmitField('Опубликовать')
