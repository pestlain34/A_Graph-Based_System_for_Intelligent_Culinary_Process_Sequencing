import os
from uuid import uuid4

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, current_app
)
from flask_login import login_required, current_user
from psycopg import DatabaseError, IntegrityError
from werkzeug.utils import secure_filename

from app.forms.update_profile_picture_form import UpdatePictureForm
from app.forms.update_user_profile_form import UpdateUserForm
from app.profile.utils import delete_file
from db.db import get_db

bp = Blueprint('profile', __name__, url_prefix='/profile')


@bp.route('/profile', methods=['GET', 'POST'])
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
                        SET username      = %s,
                            email         = %s,
                            birthday_date = %s
                        WHERE user_id = %s
                        """,
                        (form.username.data, form.email.data, form.birthday_date.data, current_user.id)
                    )
                    db.commit()
            except (DatabaseError, IntegrityError):
                db.rollback()
                flash("Произошла ошибка сохранения данных пользователя", 'danger')
                return render_template("profile/profile.html", form=form, current_user=current_user)

            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.birthday_date = form.birthday_date.data

            flash("Изменение данных профиля прошло успешно", 'success')
            return redirect(url_for('profile.profile'))
    return render_template("profile/profile.html", form=form, current_user=current_user)


@bp.route('/update_profile_picture', methods=['GET', 'POST'])
@login_required
def update_profile_picture():
    form = UpdatePictureForm()
    if request.method == 'GET':
        return render_template('profile/update_picture.html', form=form)
    if form.validate_on_submit():
        f = form.image.data
        if not f:
            flash("Файл не выбран", "warning")
            return render_template('profile/update_picture.html', form=form)

        os.makedirs(os.path.join(current_app.static_folder, 'image/profile_photo'), exist_ok=True)
        filename = secure_filename(f.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique = f"{uuid4().hex}.{ext}" if ext else uuid4().hex

        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT image
                    FROM user_of_app
                    WHERE user_id = %s
                    """,
                    (current_user.id,)
                )
                data_of_user = cursor.fetchone()

            curimage = data_of_user['image']
            imgg = os.path.join('image/profile_photo', unique).replace('\\', '/')
            mimee = f.mimetype

            with db.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE user_of_app
                    SET image          = %s,
                        image_mime     = %s,
                        image_filename = %s
                    WHERE user_id = %s
                    """,
                    (imgg, mimee, filename, current_user.id)
                )
            db.commit()
            if curimage != "image/profile_photo/1250689.png":
                delete_file(current_app.static_folder, curimage)

            current_user.image = imgg
            current_user.image_mime = mimee
            current_user.image_filename = filename

        except (DatabaseError, IntegrityError):
            db.rollback()
            flash("Ошибка, при смене фото профиля", 'danger')
            return redirect(url_for('profile.profile'))

        flash("Успешная смена фото профиля", 'success')
        dest = os.path.join(current_app.static_folder, 'image/profile_photo', unique)
        f.save(dest)
        return redirect(url_for('profile.profile'))
    return render_template('profile/update_picture.html', form=form)
