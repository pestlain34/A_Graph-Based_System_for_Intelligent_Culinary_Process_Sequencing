from functools import wraps
from urllib.parse import urlsplit

from flask import render_template, request, url_for, redirect, flash, Blueprint, current_app
from flask_login import current_user
from psycopg2 import DatabaseError, IntegrityError

from app.forms.add_category_form import AddCategoryForm
from app.forms.approve_form import ApproveForm
from app.forms.ban_user_form import Ban_User_Form
from app.forms.delete_form import DeleteForm
from app.forms.give_admin_form import Give_Admin
from app.forms.reject_form import RejectForm
from app.forms.unban_user_form import Unban_User_Form
from app.my_recipes.utils import delete_file
from db.db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


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
                SELECT user_id, username, date_of_registr, birthday_date, email, role, is_banned
                FROM user_of_app
                ORDER BY user_id
                """
            )
            users_data = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении данных о пользователях", 'danger')
        return render_template("admin/main_admin_page.html")

    ban_form = Ban_User_Form()
    give_admin_form = Give_Admin()
    unban_form = Unban_User_Form()
    return render_template("admin/work_with_users.html", users_data=users_data, ban_form=ban_form,
                           give_admin_form=give_admin_form, unban_form=unban_form)


@bp.route("/look_profile/<int:user_id>")
@admin_required
def look_profile(user_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, email, birthday_date, date_of_registr
                FROM user_of_app
                WHERE user_id = %s
                """,
                (user_id,)
            )
            user_data = cursor.fetchone()

    except (DatabaseError, IntegrityError):
        flash("Ошибка получения данных пользователя", 'danger')
        return redirect(url_for('admin.work_with_users'))

    return render_template("admin/look_profile.html", user_data=user_data)


@bp.route("/give_admin/<int:user_id>", methods=['POST'])
@admin_required
def give_admin(user_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, role
                FROM user_of_app
                WHERE user_id = %s
                """,
                (user_id,)
            )
            user_role = cursor.fetchone()
        if user_role['role'] == "admin":
            flash("Данный пользователь уже является администратором", 'info')
            return redirect(url_for('admin.work_with_users'))
        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_of_app
                SET role = %s
                WHERE user_id = %s
                """,
                ("admin", user_id,)
            )
        db.commit()
        flash(f'Юзеру {user_role['username']} были успешно выданы права администратора', 'success')
    except (DatabaseError, IntegrityError):
        flash("Ошибка при выдаче прав админа пользователю", 'danger')
        return redirect(url_for('admin.work_with_users'))
    return redirect(url_for('admin.work_with_users'))


@bp.route("/ban_user/<int:user_id>", methods=['POST'])
@admin_required
def ban_user(user_id):
    if user_id == current_user.id:
        flash("Вы не можете забанить самого себя", 'danger')
        return redirect(url_for('admin.work_with_users'))
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, role
                FROM user_of_app
                WHERE user_id = %s
                """,
                (user_id,)
            )
            user_role_data = cursor.fetchone()
        if not user_role_data:
            flash("Пользователь не найден", 'danger')
            return redirect(url_for('admin.work_with_users'))

        if user_role_data['role'] == "admin":
            flash("Вы не можете забанить админа", 'info')
            return redirect(url_for('admin.work_with_users'))
        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_of_app
                SET is_banned = TRUE
                WHERE user_id = %s
                """,
                (user_id,)
            )
        db.commit()
        flash(f'Пользователь {user_role_data['username']} успешно забанен', 'success')
    except (DatabaseError, IntegrityError):
        flash("Ошибка при блокировке пользователя", 'danger')
        return redirect(url_for('admin.work_with_users'))

    return redirect(url_for('admin.work_with_users'))


@bp.route("/unban_user/<int:user_id>", methods=['POST'])
@admin_required
def unban_user(user_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, role
                FROM user_of_app
                WHERE user_id = %s
                """,
                (user_id,)
            )
            user_role_data = cursor.fetchone()
        if not user_role_data:
            flash("Пользователь не найден", 'danger')
            return redirect(url_for('admin.work_with_users'))

        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_of_app
                SET is_banned = FALSE
                WHERE user_id = %s
                """,
                (user_id,)
            )
        db.commit()
        flash(f'Пользователь {user_role_data['username']} успешно разбанен', 'success')
    except (DatabaseError, IntegrityError):
        flash("Ошибка при разблокировке пользователя", 'danger')
        return redirect(url_for('admin.work_with_users'))

    return redirect(url_for('admin.work_with_users'))


@bp.route("/work_with_category")
@admin_required
def work_with_category():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT category_id, name
                FROM category
                ORDER BY category_id
                """
            )
            category_data = cursor.fetchall()
    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении данных о категориях", 'danger')
        return redirect(url_for('admin.main_admin_page'))
    add_form = AddCategoryForm()
    delete_form = DeleteForm()
    return render_template("admin/work_with_category.html", category_data=category_data, add_form=add_form,
                           delete_form=delete_form)


@bp.route("/add_category", methods=['GET', 'POST'])
@admin_required
def add_category():
    form = AddCategoryForm()
    if form.validate_on_submit():
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO category (name)
                    VALUES (%s)
                    """,
                    (form.name.data,)
                )
            db.commit()

        except (DatabaseError, IntegrityError):
            db.rollback()
            flash("Ошибка при добавлении новой категории", 'danger')
            return redirect(url_for('admin.work_with_category'))
        flash("Категория успешно добавлена", 'success')
        return redirect(url_for('admin.work_with_category'))
    return render_template('admin/add_category.html', form=form)


@bp.route("/delete_category/<int:category_id>", methods=['POST'])
@admin_required
def delete_category(category_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                DELETE
                FROM category
                WHERE category_id = %s
                """,
                (category_id,)
            )
        db.commit()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при удалении категории", 'danger')
        return redirect(url_for('admin.work_with_category'))
    flash("Произошло успешное удаление категории", 'success')
    return redirect(url_for('admin.work_with_category'))


@bp.route("/delete_recipe/<int:recipe_id>", methods=['POST'])
@admin_required
def delete_recipe(recipe_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT image
                FROM recipe
                WHERE recipe_id = %s
                """,
                (recipe_id,)
            )
            row = cursor.fetchone()
        relpath = row['image']
        delete_file(current_app.static_folder, relpath)
        with db.cursor() as cursor:
            cursor.execute(
                """
                DELETE
                FROM recipe
                WHERE recipe_id = %s
                """,
                (recipe_id,)
            )
        db.commit()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при удалении рецепта", 'danger')
        next = request.args.get('next')
        if not next or urlsplit(next).netloc != '':
            next = url_for('index.index')
        return redirect(next)

    flash("Успешное удаление рецепта", 'success')
    next = request.args.get('next')
    if not next or urlsplit(next).netloc != '':
        next = url_for('index.index')
    return redirect(next)


@bp.route("/work_with_recipes")
@admin_required
def work_with_recipes():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_id, creation_date, difficulty, title, description, status_of_recipe
                FROM recipe
                """
            )
            recipes_data = cursor.fetchall()
    except (DatabaseError, IntegrityError):
        flash("Ошибка при отображении данных о рецептах", 'danger')
        return redirect(url_for('admin.main_admin_page'))
    delete_form = DeleteForm()
    return render_template("admin/work_with_recipes.html", recipes_data=recipes_data, delete_form=delete_form)


@bp.route("/work_with_publications")
@admin_required
def work_with_publications():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_id, creation_date, difficulty, title, description, status_of_recipe
                FROM recipe
                WHERE status_of_recipe = %s
                ORDER BY recipe_id
                """,
                ("under_consideration",)
            )
            wait_to_be_publicated = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении рецептов на рассмотрении", 'danger')
        return redirect(url_for('admin.main_admin_page'))
    approve_form = ApproveForm()
    reject_form = RejectForm()
    return render_template("admin/work_with_publications.html", wait_to_be_publicated=wait_to_be_publicated,
                           approve_form=approve_form, reject_form=reject_form)


@bp.route("/approve_recipe/<int:recipe_id>", methods=['POST'])
@admin_required
def approve_recipe(recipe_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recipe
                SET status_of_recipe = %s
                WHERE recipe_id = %s
                """,
                ("publicated", recipe_id,)
            )
        db.commit()
    except (DatabaseError, IntegrityError):
        flash("Ошиюка при одобрении рецепта на публикацию", 'danger')
        return redirect(url_for('admin.work_with_publications'))
    flash("Поздравляем, вы успешно одобрили на публикацию рецепт", 'success')
    return redirect(url_for('admin.work_with_publications'))


@bp.route("/reject_recipe/<int:recipe_id>", methods=['POST'])
@admin_required
def reject_recipe(recipe_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recipe
                SET status_of_recipe = %s
                WHERE recipe_id = %s
                """,
                ("rejected", recipe_id,)
            )
        db.commit()
    except (DatabaseError, IntegrityError):
        flash("Ошибка при отклонении рецепта на публикацию", 'danger')
        return redirect(url_for('admin.work_with_publications'))
    flash("Поздравляем, вы успешно отклонили на публикацию рецепт", 'success')
    return redirect(url_for('admin.work_with_publications'))
