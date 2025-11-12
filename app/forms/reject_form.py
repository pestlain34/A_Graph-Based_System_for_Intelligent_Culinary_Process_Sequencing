from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class RejectForm(FlaskForm):
    submit = SubmitField('Отклонить')
