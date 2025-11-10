from functools import wraps

from flask import render_template, request, url_for, redirect, flash, abort, Blueprint, current_app
from flask_login import current_user
from psycopg2 import DatabaseError, IntegrityError

from app.forms.ban_user_form import Ban_User_Form
from app.forms.give_admin_form import Give_Admin
from app.forms.look_profile_form import Look_User
from db.db import get_db

bp = Blueprint("admin", __name__, url_prefix = "/admin")

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, 'role', None) != "admin":
            flash("У вас нет прав доступа к этой странице", 'danger')
            return redirect(url_for('index.index'))
        return func(*args, **kwargs)
    return wrapper

@bp.route("/")
@admin_required
def main_admin_page():
    return render_template("admin/main_admin_page.html")

@bp.route("/work_with_users")
@admin_required
def work_with_users():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username, date_of_registr, birthday_date, email, role FROM user_of_app ORDER BY user_id
                """
            )
            users_data = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении данных о пользователях", 'danger')
        return render_template("admin/main_admin_page.html")

    ban_form = Ban_User_Form()
    give_admin_form = Give_Admin()
    look_user_form = Look_User()
    return render_template("admin/work_with_users.html", users_data=users_data, ban_form=ban_form, give_admin_form=give_admin_form, look_user_form=look_user_form)

@bp.route("/look_profile/<int:user_id>")
@admin_required
def look_profile(user_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, email, birthday_date, date_of_registr FROM user_of_app WHERE user_id = %s
                """,
                (user_id,)
            )
            user_data = cursor.fetchone()

    except (DatabaseError, IntegrityError):
        flash("Ошибка получения данных пользователя", 'danger')
        return redirect(url_for('admin.work_with_users'))

    return render_template("admin/look_profile.html", user_data=user_data)
