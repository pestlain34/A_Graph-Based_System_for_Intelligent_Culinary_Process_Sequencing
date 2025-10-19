
from flask import Blueprint, render_template, request, redirect, url_for
bp = Blueprint('index',__name__)

@bp.route('/')
def index():
    return render_template('index/index.html')



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