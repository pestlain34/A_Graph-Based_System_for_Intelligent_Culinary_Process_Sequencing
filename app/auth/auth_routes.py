from urllib.parse import urlsplit

import psycopg2
from psycopg2 import DatabaseError, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from app.auth.reset_password import generate_password_reset_token, send_password_reset_email, \
    verify_password_reset_token
from app.forms.register_form import RegisterForm
from app.forms.reset_password_form import ResetPasswordForm
from app.forms.reset_request_form import RequestResetForm
from app.user import User
from db.db import get_db
from flask_login import current_user, login_user, logout_user, login_required
from app.forms.login_form import LoginForm

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    regform = RegisterForm()
    if regform.validate_on_submit():
        db = get_db()
        hashed_password = generate_password_hash(regform.password.data)
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_of_app (username, password, email, birthday_date)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (regform.username.data, hashed_password, regform.email.data, regform.birthday_date.data)
                )
                db.commit()
        except (IntegrityError, DatabaseError):
            db.rollback()
            flash('Произошла ошибка при регистрации', 'danger')
            return render_template('auth/registration.html', title='Регистрация', form=regform)

        flash(f'Регистрация пользователя {regform.username.data} прошла успешно', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/registration.html', title='Регистрация', form=regform)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    loginform = LoginForm()
    if loginform.validate_on_submit():
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id,
                           username,
                           password,
                           role,
                           email,
                           birthday_date,
                           date_of_registr,
                           is_banned,
                           image,
                           image_mime,
                           image_filename
                    FROM user_of_app
                    WHERE username = %s
                    """,
                    (loginform.username.data,)
                )
                data = cursor.fetchone()
        except (DatabaseError, IntegrityError):
            flash('Ошибка сервера, попробуйте позже', 'danger')
            return render_template('auth/login.html', title='Вход', form=loginform)
        if data is None or not check_password_hash(data['password'], loginform.password.data):
            flash(f'Неудачная попытка, попробуйте еще раз', 'danger')
            return render_template('auth/login.html', title='Вход', form=loginform)
        user_id, username, password, role, email, birthday_date, date_of_registr, is_banned, image, image_mime, image_filename = data['user_id'], data[
            'username'], data['password'], data['role'], data['email'], data['birthday_date'], data['date_of_registr'], \
        data['is_banned'], data['image'], data['image_mime'], data['image_filename']
        if is_banned:
            flash("Ваша учетная запись заблокирована", 'danger')
            return render_template('auth/login.html', title='Вход', form=loginform)
        user = User(user_id, username, password, role, email, birthday_date, date_of_registr, is_banned, image, image_mime, image_filename)
        login_user(user, remember=loginform.remember_me.data)
        flash(f'Поздравляем, {user.username}, вы успешно вошли в систему', 'success')
        next = request.args.get('next')
        if not next or urlsplit(next).netloc != '':
            next = url_for('index.index')
        return redirect(next)
    return render_template('auth/login.html', title='Вход', form=loginform)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index.index'))


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id
                FROM user_of_app
                WHERE email = %s
                """,
                (form.email.data,)
            )
            row = cursor.fetchone()
        if row:
            user_id = row['user_id']
            token = generate_password_reset_token(user_id)
            send_password_reset_email(form.email.data, token)

        flash('Если почта существует, вы получите письмо на почту', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)


@bp.route('/reset_password_with_token/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_password_reset_token(token)
    if user_id is None:
        flash('Ссылка для смены пароля недействительная или истекла', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        new_password_hash = generate_password_hash(form.password.data)
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE user_of_app
                    SET password = %s
                    WHERE user_id = %s
                    """,
                    (new_password_hash, user_id)
                )
                db.commit()
        except (IntegrityError, DatabaseError):
            db.rollback()
            flash("При смене пароля произошла ошибка", 'danger')
            return render_template('auth/reset_password_with_token.html', form=form)

        flash("Пароль был успешно изменен,можете авторизироваться", 'success')
        return redirect(url_for('auth.login'))
    return render_template("auth/reset_password_with_token.html", form=form)
