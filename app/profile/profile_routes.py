import mimetypes
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
from app.services.utils import make_s3_key, generate_s3_url, delete_object_s3, upload_fileobj_to_s3
from db.db import get_db

bp = Blueprint('profile', __name__, url_prefix='/profile')


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateUserForm()
    bucket = current_app.config['S3_BUCKET']
    if current_user.image:
        image_url = generate_s3_url(bucket, current_user.image, expires_in=3600, public = False)
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
    return render_template("profile/profile.html", form=form, current_user=current_user, image_url = image_url)


@bp.route('/update_profile_picture', methods=['GET', 'POST'])
@login_required
def update_profile_picture():
    form = UpdatePictureForm()
    if request.method == 'GET':
        return render_template('profile/update_picture.html', form=form)
    if form.validate_on_submit():
        f = form.image.data
        old_key = current_user.image
        if not f:
            flash("Файл не выбран", "warning")
            return render_template('profile/update_picture.html', form=form)

        bucket = current_app.config['S3_BUCKET']
        content_type = f.mimetype or mimetypes.guess_type(f)[0]
        image_filename_new = secure_filename(f.filename or '')
        new_image = make_s3_key('profile_photo', getattr(f, 'filename', 'upload'))
        uploaded = False
        try:
            uploaded = upload_fileobj_to_s3(f.stream, bucket, new_image, content_type = content_type, public = False)
            if not uploaded:
                flash("Не удалось загрузить изображение на сервер", 'danger')
                return render_template('profile/update_picture.html', form=form)

            db = get_db()
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE user_of_app
                    SET image          = %s,
                        image_mime     = %s,
                        image_filename = %s
                    WHERE user_id = %s
                    """,
                    (new_image, content_type, image_filename_new, current_user.id)
                )
            db.commit()
            if old_key and old_key != new_image and old_key != "photo_2025-12-20_01-36-59.jpg":
                delete_object_s3(bucket, old_key)


            current_user.image = new_image
            current_user.image_mime = content_type
            current_user.image_filename = image_filename_new

        except (DatabaseError, IntegrityError):
            db.rollback()
            flash("Ошибка, при смене фото профиля", 'danger')
            if uploaded:
                delete_object_s3(bucket, new_image)
            return redirect(url_for('profile.profile'))


        flash("Успешная смена фото профиля", 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/update_picture.html', form=form)
