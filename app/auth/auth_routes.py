from urllib.parse import urlsplit

import psycopg2
from psycopg2 import DatabaseError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from app.forms.register_form import RegisterForm
from app.user import User
from db.db import get_db
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

bp = Blueprint('auth', __name__, url_prefix='/auth')
from app.forms.login_form import LoginForm


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
        except psycopg2.IntegrityError as e:
            db.rollback()
            flash('Произошла ошибка при регистрации', 'danger')
            return render_template('registration.html', title='Регистрация', form=regform)

        flash(f'Регистрация пользователя {regform.username.data} прошла успешно', 'success')
        return redirect(url_for('auth.login'))
    return render_template('registration.html', title='Регистрация', form=regform)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    loginform = LoginForm()
    if loginform.validate_on_submit():
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username, password, role
                    FROM user_of_app
                    WHERE username = %s
                    """,
                    (loginform.username.data,)
                )
                data = cursor.fetchone()
        except DatabaseError:
            flash('Ошибка сервера, попробуйте позже', 'danger')
            return render_template('auth/login.html', title='Вход', form=loginform)
        if data is None or not check_password_hash(data['password'], loginform.password.data):
            flash(f'Неудачная попытка, попробуйте еще раз', 'danger')
            return render_template('auth/login.html', title='Вход', form=loginform)
        user_id, username, password, role = data['user_id'], data['username'], data['password'], data['role']
        user = User(user_id, username, password, role)
        login_user(user, remember=loginform.remember_me.data)
        flash(f'Поздравляем, {user.username}, вы успешно вошли в систему', 'success')
        next = request.args.get('next')
        if not next or urlsplit(next).netloc != '':
            next = url_for('index')
        return redirect(next)
    return render_template('auth/login.html', title='Вход', form=loginform)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index'))
