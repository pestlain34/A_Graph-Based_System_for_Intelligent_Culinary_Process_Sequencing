from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField


class SearchForm(FlaskForm):
    recipe_type = SelectField('Тип рецепта', choices = [], coerce=int)
    ingredient = SelectField('Ингредиент', choices=[], coerce=int)
    category = SelectField('Категория', choices=[], coerce=int)
    submit = SubmitField('Найти')
