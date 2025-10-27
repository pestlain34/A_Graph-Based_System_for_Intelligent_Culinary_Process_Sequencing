from collections import defaultdict

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
        session['recipe_data'] = {
            'title': form.title.data,
            'description': form.description.data,
            'recipe_type_id': form.recipe_type.data,
            'difficulty': form.difficulty.data,
            'user_id': current_user.id
        }
        session['steps'] = []
        return redirect(url_for('index.create_step'))

    return render_template('index/create_recipe.html', form = form)

@bp.route('/create_step', methods = ['GET' , 'POST'])
@login_required
def create_step():
    if 'steps' not in session:
        session['steps'] = []
    if 'recipe_data' not in session:
        flash("Сначала вам нужно заполнить сведения о рецепте")
        return redirect(url_for('index.create_recipe'))
    form = CreateStep_form()
    steps = session.get('steps', [])
    form.prev_steps.choices = [(i , step['name']) for i, step in enumerate(steps)]
    if form.validate_on_submit():
        step_data = {
            'name': form.name.data,
            'duration': form.duration.data,
            'type_of': form.type_of.data,
            'description': form.description.data,
            'prev_steps': list(map(int, form.prev_steps.data)) if form.prev_steps.data else []
        }
        steps.append(step_data)
        session['steps'] = steps

        if form.add_another_step.data:
            flash('Этап добавлен', 'success')
            return redirect(url_for('index.create_step'))

        if form.end_recipe.data:
            db = get_db()
            recipe_data = session.get('recipe_data', {})
            steps_data = session.get('steps', [])
            try:
                with db.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO recipe (difficulty, title , description , user_id, recipe_type_id) VALUES (%s, %s, %s, %s, %s)
                        RETURNING recipe_id
                        """,
                        (recipe_data['difficulty'], recipe_data['title'], recipe_data['description'], recipe_data['user_id'],recipe_data['recipe_type_id'])
                    )
                    row = cursor.fetchone()
                    recipe_id = row['recipe_id']

                    index_to_dbid = {}
                    for idx , s in enumerate(steps_data):
                        cursor.execute(
                            """
                            INSERT INTO recipe_step (name, duration, type_of, description, recipe_id) VALUES (%s, %s, %s, %s, %s)
                            RETURNING recipe_step_id
                            """,
                            (s['name'] , s['duration'], s['type_of'], s['description'], recipe_id)
                        )
                        row2 = cursor.fetchone()
                        index_to_dbid[idx] = row2['recipe_step_id']

                    for idx,s in enumerate(steps_data):
                        cur_db_id = index_to_dbid[idx]
                        for prev_index in s.get('prev_steps', []):
                            prev_db_id = index_to_dbid.get(prev_index)
                            if prev_db_id:
                                cursor.execute(
                                    """
                                    INSERT INTO deps_of_step (recipe_step_id, prev_step_id) VALUES (%s, %s)
                                    """,
                                    (cur_db_id, prev_db_id)
                                )
                db.commit()
            except psycopg2.IntegrityError:
                db.rollback()
                flash('Ошибка при сохранении рецепта в базу данных, попробуйте еще раз')
                return render_template('index/create_step.html', form = form)



            session.pop('steps', None)
            session.pop('recipe_data', None)
            flash('Рецепт успешно создан', 'success')
            return redirect(url_for('index.view_recipe', recipe_id= recipe_id))

    return render_template('index/create_step.html', form = form)

@bp.route('/view_recipe<int:recipe_id>')
def view_recipe(recipe_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT difficulty, title, description, user_id, recipe_type_id FROM recipe WHERE recipe_id = %s
                """,
                (recipe_id,)
            )
            recipe = cursor.fetchone()
            if recipe is None:
                flash("Такого рецепта нет в базе рецептов", 'danger')
                return render_template('404.html'), 404

            cursor.execute(
                """
                SELECT recipe_step_id, name, duration, type_of, description, recipe_id FROM recipe_step WHERE recipe_id = %s ORDER BY recipe_step_id
                """,
                (recipe_id,)
            )
            steps = cursor.fetchall()

            cursor.execute(
                """
                SELECT recipe_step_id, prev_step_id FROM deps_of_step WHERE recipe_step_id IN (SELECT recipe_step_id
                FROM recipe_step WHERE recipe_id = %s)
                """,
                (recipe_id,)
            )
            deps = cursor.fetchall()
    except psycopg2.DatabaseError:
        db.rollback()
        flash("Ошибка сервера при загрузке рецепта", 'danger')
        return render_template("error.html"), 500

    deps_map = defaultdict(list)
    for d in deps:
        deps_map[d['recipe_step_id']].append(d['prev_step_id'])

    id_to_index = {step['recipe_step_id']: i + 1 for i, step in enumerate(steps)}
    id_to_name = {step['recipe_step_id']: step['name'] for step in steps}
    for step in steps:
        previd_list = deps_map.get(step['recipe_step_id'] , [])
        step['prev_numbers'] = [id_to_index[previd] for previd in previd_list if previd in id_to_index]
        step['prev_names'] = [id_to_name[previd] for previd in previd_list if previd in id_to_name]

    total_time = sum(s['duration'] for s in steps)
    return render_template("recipe/view_recipe.html", recipe = recipe, steps = steps, total_time = total_time)



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