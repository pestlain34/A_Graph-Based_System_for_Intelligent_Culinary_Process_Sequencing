from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, validators, SubmitField


class IngredientForm(FlaskForm):
    ingredient = SelectField('Ингредиент', choices=[], coerce=int, validators=[validators.InputRequired()])
    amount = IntegerField('Количество', validators=[validators.InputRequired(), validators.NumberRange(min=1)])
    edin_izmer = SelectField('Единица измерения', choices=[
        ('g', 'г'),
        ('kg', 'кг'),
        ('ml', 'мл'),
        ('l', 'л'),
        ('pcs', 'шт'),
    ], validators=[validators.InputRequired()])
    add_another_ingredient = SubmitField('Добавить еще один ингредиент')
    go_next = SubmitField('Далее')
