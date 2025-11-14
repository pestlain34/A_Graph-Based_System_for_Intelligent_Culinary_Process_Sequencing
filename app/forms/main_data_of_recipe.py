import os
import io

from PIL import UnidentifiedImageError
from PIL import Image
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, validators, SubmitField, TextAreaField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import InputRequired, ValidationError
from flask_wtf.file import FileAllowed, FileRequired, FileField

ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif', 'webp'}

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
    image = FileField('Фото блюда', validators = [FileRequired(), FileAllowed(list(ALLOWED_EXTENSIONS), 'Только изображения')])
    go_next = SubmitField('Далее')

    def validate_image(self, field):
        f = field.data
        if not f:
            raise ValidationError("Файл не передан")
        filename = secure_filename(getattr(f, 'filename', '') or '')
        if not filename:
            raise ValidationError("Нет имени файла")
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError("Недопустимое расширение")
        max_size = 2 * 1024 * 1024
        try:
            f.stream.seek(0, os.SEEK_END)
            size = f.stream.tell()
            f.stream.seek(0)
        except Exception:
            size = None

        if size and size > max_size:
            raise ValidationError("Файл слишком большой, он не должен превышать 2МБ")

        try:
            img = Image.open(f.stream)
            img.verify()
        except UnidentifiedImageError:
            f.stream.seek(0)
            raise ValidationError("Файл не распознаётся как изображение")

        f.stream.seek(0)
