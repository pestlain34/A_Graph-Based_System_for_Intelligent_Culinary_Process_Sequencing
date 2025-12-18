from flask_wtf import FlaskForm
from wtforms import StringField, validators, TextAreaField
from wtforms.fields.simple import SubmitField


class AddCategoryForm(FlaskForm):
    name = StringField("Название категории", validators=[validators.DataRequired(message="Введите данные"),
                                                         validators.Length(min=10, max=100,
                                                                           message="Длина должна быть в пределах [10,100]")],
                       render_kw={
                           "placeholder": "Например: Молочная продукция"})
    submit = SubmitField("Добавить категорию")
