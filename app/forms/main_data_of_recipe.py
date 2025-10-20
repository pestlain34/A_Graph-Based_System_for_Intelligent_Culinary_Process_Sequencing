from flask_wtf import FlaskForm
from wtforms import StringField, validators, SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import InputRequired


class Main_data_of_recipe_form(FlaskForm):
    title = StringField('Название рецепта', validators = [validators.DataRequired(message = "Введите название рецепта")],
    render_kw={"placeholder": "Например: Борщ, Паста карбонара"})
    recipe_type = SelectField('Тип рецепта', choices = [
        ('салаты', 'салаты'),
        ('основные блюда', 'основные блюда'),
        ('гарниры', 'гарниры'),
        ('закуски', 'закуски'),
        ('соусы', 'соусы'),
        ('десерты', 'десерты'),
        ('напитки', 'напитки')
    ],  validators = [validators.DataRequired(message = "Выберите тип рецепта")])
    difficulty = SelectField('Сложность рецепта', choices = [
        ('сложная', 'сложная'),
        ('средняя', 'средняя'),
        ('лёгкая', 'лёгкая')
    ], validators = [validators.DataRequired(message = "Выберите сложность рецепта")])
    total_time = IntegerField('Время приготовления блюда(мин)', validators = [InputRequired(message="Введите время в минутах")],
    render_kw={"placeholder": "Например: 45"})
    go_next = SubmitField('Далее')