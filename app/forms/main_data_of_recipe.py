from flask_wtf import FlaskForm
from wtforms import StringField, validators, SubmitField, TextAreaField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import InputRequired


class Main_data_of_recipe_form(FlaskForm):
    title = StringField('Название рецепта', validators = [validators.DataRequired(message = "Введите название рецепта")],
    render_kw={"placeholder": "Например: Борщ, Паста карбонара"})
    description = TextAreaField('Описание рецепта', validators=[validators.DataRequired(message = "Напишите описание рецепта")],
    render_kw={"placeholder": "Например: Очень простое и очень вкусное блюдо не требующее особых навыков готовки"})
    recipe_type = SelectField('Тип рецепта', choices= [], coerce = int, validators = [validators.DataRequired(message = "Выберите тип рецепта")])
    difficulty = SelectField('Сложность рецепта', choices = [
        ('сложная', 'сложная'),
        ('средняя', 'средняя'),
        ('лёгкая', 'лёгкая')
    ], validators = [validators.DataRequired(message = "Выберите сложность рецепта")])
    go_next = SubmitField('Далее')