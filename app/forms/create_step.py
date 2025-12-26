from flask_wtf import FlaskForm
from wtforms import StringField, validators, SubmitField
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import NumberRange


class CreateStep_form(FlaskForm):
    name = StringField('Название этапа', validators=[validators.DataRequired(message="Введите название этапа")],
                       render_kw={"placeholder": "Например: Взбитие яйца для теста"})
    duration = IntegerField('Длительность этапа в минутах',
                            validators=[validators.InputRequired(message="Введите длительность этапа"),
                                        NumberRange(min=1, message="Длительность должна быть минимум 1 минута, максимум 1000", max=1000)],
                            render_kw={"placeholder": "Например: 45"})
    type_of = SelectField('Тип этапа', choices=[
        ('active', 'Активный (делаем что-то сами)'),
        ('passive', 'Пассивный (ждем, пока что-то приготовится)')
    ], validators=[validators.DataRequired(message="Выберите тип этапа")])
    description = TextAreaField('Описание этапа рецепта',
                                validators=[validators.DataRequired(message="Напишите описание рецепта")],
                                render_kw={
                                    "placeholder": "Например: Берём аккуратно яйцо, разбиваем его напополам, начинаем взбивать аккуратными интенсивными движениями"})
    prev_steps = SelectMultipleField('Предыдущие обязательные этапы(если есть)', choices=[], coerce=int)
    add_another_step = SubmitField('Добавить еще один этап')
    end_recipe = SubmitField('Завершить рецепт')
