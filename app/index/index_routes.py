from collections import defaultdict

import psycopg2
from flask_login import login_required, current_user
from psycopg2 import IntegrityError, DatabaseError

from app.forms.add_to_planner_form import AddToPlannerForm
from app.forms.main_data_of_recipe import Main_data_of_recipe_form
from app.forms.create_step import CreateStep_form
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.planner.planner_routes import add_to_planner
from db.db import get_db

bp = Blueprint('index',__name__)

@bp.route('/')
def index():
    session.pop('steps', None)
    session.pop('recipe_data', None)
    add_to_planner_form = AddToPlannerForm()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_id, title, description, difficulty, creation_date
                FROM recipe
                ORDER BY creation_date DESC
                """
            )
            all_recipes = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении данных о рецептах из базы", 'danger')
        all_recipes = []
    return render_template('index/index.html', all_recipes=all_recipes, add_to_planner_form=add_to_planner_form)







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