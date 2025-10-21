from flask_login import login_required

from app.forms.main_data_of_recipe import Main_data_of_recipe_form
from app.forms.create_step import CreateStep_form
from flask import Blueprint, render_template, request, redirect, url_for, session

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
    if form.validate_on_submit():
        session['recipe_data'] = {
            'title': form.title.data,
            'description': form.description.data,
            'recipe_type': form.recipe_type.data,
            'difficulty': form.difficulty.data,
            'total_time': form.total_time.data
        }
        return redirect(url_for('index.create_step'))
    return render_template('index/create_recipe.html', form = form)

@bp.route('/create_step', methods = ['GET' , 'POST'])
@login_required
def create_step():
    if 'steps' not in session:
        session.pop('steps', None)
    form = CreateStep_form()
    steps = session.get('steps', [])
    form.prev_steps.choices = [(i , step['name']) for i, step in enumerate(steps)]
    if form.validate_on_submit():
        step_data = {
            'name': form.name.data,
            'duration': form.duration.data,
            'type_of': form.type_of.data,
            'description': form.description.data,
            'prev_steps': form.prev_steps.data
        }
        steps.append(step_data)
        if form.add_another_step.data:
            session['steps'] = steps
            return redirect(url_for('index.create_step'))

        if form.end_recipe.data:
            session.pop('steps', None)
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