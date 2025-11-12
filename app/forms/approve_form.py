from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class ApproveForm(FlaskForm):
    submit = SubmitField('Одобрить')
