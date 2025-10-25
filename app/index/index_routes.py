import psycopg2
from flask_login import login_required, current_user

from app.forms.main_data_of_recipe import Main_data_of_recipe_form
from app.forms.create_step import CreateStep_form
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from db.db import get_db

bp = Blueprint('index',__name__)

@bp.route('/')
def index():
    session.pop('steps', None)
    session.pop('recipe_data', None)
    return render_template('index/index.html')

@bp.route('/create_recipe', methods = ['GET', 'POST'])
@login_required
def create_recipe():
    form = Main_data_of_recipe_form()
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT recipe_type_id, recipe_type_name FROM recipe_type ORDER BY recipe_type_name
            """
        )
        rows = cursor.fetchall()
    choices = [(row['recipe_type_id'] , row['recipe_type_name']) for row in rows]
    form.recipe_type.choices = choices
    if form.validate_on_submit():
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO recipe (title, description, recipe_type_id, difficulty, user_id) VALUES (%s , %s , %s , %s, %s)
                    RETURNING recipe_id
                    """,
                    (form.title.data, form.description.data, form.recipe_type.data, form.difficulty.data, current_user.id)
                )
                row = cursor.fetchone()
            db.commit()
            recipe_id = row['recipe_id']
            session['recipe_data'] = {
                'recipe_id': recipe_id,
                'title': form.title.data,
                'description': form.description.data,
                'recipe_type_id': form.recipe_type.data,
                'difficulty': form.difficulty.data
            }
            return redirect(url_for('index.create_step'))
        except psycopg2.IntegrityError:
            db.rollback()
            flash("Произошла ошибка при попытке вставки", 'danger')

    return render_template('index/create_recipe.html', form = form)

@bp.route('/create_step', methods = ['GET' , 'POST'])
@login_required
def create_step():
    if 'steps' not in session:
        session['steps'] = []
    form = CreateStep_form()
    db = get_db()
    steps = session.get('steps', [])
    form.prev_steps.choices = [(i , step['name']) for i, step in enumerate(steps)]
    if form.validate_on_submit():
        recipe_data = session.get('recipe_data', {})
        recipe_id = recipe_data.get('recipe_id')
        if not recipe_id:
            flash('Не найден идентификатор рецепта. Сначала создайте рецепт.', 'danger')
            return redirect(url_for('index.create_recipe'))
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO recipe_step (name , duration, type_of, description, recipe_id) VALUES (%s, %s, %s, %s, %s)
                    RETURNING recipe_step_id
                    """,
                    (form.name.data, form.duration.data, form.type_of.data, form.description.data, recipe_id)
                )
                row = cursor.fetchone()
            db.commit()
        except psycopg2.DatabaseError as e:
            db.rollback()
            flash("Ошибка сервера при сохранении шага рецепта", 'danger')
            return render_template('index/create_step.html' , form = form)

        new_step_id = row['recipe_step_id']
        prev_indices = form.prev_steps.data or []
        try:
            with db.cursor() as cursor:
                for idx in prev_indices:
                    try:
                        prev_db_id = steps[idx].get('db_id')
                    except (IndexError, AttributeError):
                        continue
                    if prev_db_id:
                        cursor.execute(
                            """
                            INSERT INTO deps_of_step (recipe_step_id , prev_step_id) VALUES (%s , %s)
                            """,
                            (new_step_id , prev_db_id)
                        )
            db.commit()
        except psycopg2.DatabaseError as e:
            db.rollback()
            flash("Произошла ошибка при попытке сохранить зависимость шагов", 'danger')
            return render_template('index/create_step.html' , form = form)

        step_data = {
            'name': form.name.data,
            'duration': form.duration.data,
            'type_of': form.type_of.data,
            'description': form.description.data,
            'prev_steps': form.prev_steps.data,
            'db_id' : new_step_id
        }
        steps.append(step_data)
        if form.add_another_step.data:
            session['steps'] = steps
            flash('Этап добавлен', 'success')
            return redirect(url_for('index.create_step'))

        if form.end_recipe.data:
            session.pop('steps', None)
            session.pop('recipe_data', None)
            flash('Рецепт успешно создан', 'success')
            return redirect(url_for('recipe.success'))

    return render_template('index/create_step.html', form = form)




# # @app.route('/edituser/<int:user_id>', methods=['GET', 'POST'])
# # def edit_user(user_id):
# #     # здесь должна быть проверка, имеет ли текущий пользователь право на редактирование пользователя user_id,
# #     # например это тот же самый пользователь, либо текущий пользователь является администратором,
# #     # и что пользователь user_id вообще существует
# #     with psycopg.connect(...) as con:
# #         cur = con.cursor()
# #         email, bd, rc, ws, ci = cur.execute('SELECT email, bd, rc, ws, city_id '
# #                                             'FROM "user" '
# #                                             'WHERE id = %s', (user_id,)).fetchone()
# #         cities = cur.execute('SELECT id, name '
# #                              'FROM city '
# #                              'ORDER BY name DESC').fetchall()
# #     form = EditUserForm(email=email, birth_date=bd, region_code=rc, want_spam=ws, city=ci)
# #     form.city.choices = cities
# #     if form.valdate_on_submit():
# #         # сохранить новые данные пользователя в базе данных
# #         flash('Изменения сохранены')
# #         return redirect(url_for('edit_user', user_id=user_id))
# #     return render_template('edit_user.html', title='Редактирование пользователя', form=form)
#
#

#
# @app.route('/admin', methods=['GET', 'POST'])
# @login_required
# def admin():
#     if current_user.role != 1:
#         abort(403)
#     form = AdminForm()
#     # Обработка формы и выполнение действий для администратора
#     return render_template('admin.html', title='Панель администратора', form=form)