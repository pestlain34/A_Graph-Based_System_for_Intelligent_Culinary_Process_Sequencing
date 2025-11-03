import psycopg2
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flask_login import login_required, current_user
from psycopg import DatabaseError, IntegrityError

from app.forms.update_user_profile_form import UpdateUserForm
from db.db import get_db

bp = Blueprint('profile', __name__, url_prefix = '/profile')

@bp.route('/profile', methods = ['GET', 'POST'])
@login_required
def profile():
    form = UpdateUserForm()
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.birthday_date.data = current_user.birthday_date
    elif request.method == 'POST':
        if form.validate_on_submit():
            db = get_db()
            try:
                with db.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE user_of_app
                        SET username = %s, email = %s, birthday_date = %s
                        WHERE user_id = %s
                        """,
                        (form.username.data, form.email.data, form.birthday_date.data, current_user.id)
                    )
                    db.commit()
            except (DatabaseError,IntegrityError):
                db.rollback()
                flash("Произошла ошибка сохранения данных пользователя", 'danger')
                return render_template("profile/profile.html", form = form, current_user = current_user)

            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.birthday_date = form.birthday_date.data

            flash("Изменение данных профиля прошло успешно",'success')
            return redirect(url_for('profile.profile'))
    return render_template("profile/profile.html", form = form, current_user = current_user)


