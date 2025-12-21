import os
from flask import Flask, flash, redirect, url_for, session, current_app, request
from flask.cli import load_dotenv
from flask_login import current_user, logout_user
from psycopg2 import IntegrityError, DatabaseError

from db.db import get_db
from .extensions import login_manager, bootstrap, mail
from db import db
from . import auth
from . import index
from . import profile
from . import errors
from . import my_recipes
from . import planner
from . import admin
from app.services.utils import delete_object_s3, generate_s3_url


def env_bool(name):
    if name == "True":
        return True
    return False


load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        DATABASE=os.getenv('DATABASE'),
        DB_NAME=os.getenv('DB_NAME'),
        DB_USER=os.getenv('DB_USER'),
        DB_PASSWORD=os.getenv('DB_PASSWORD'),
        DB_HOST=os.getenv('DB_HOST'),
        DB_PORT=os.getenv('DB_PORT')
    )
    app.config.from_mapping(
        MAIL_SERVER=os.getenv('MAIL_SERVER'),
        MAIL_PORT=int(os.getenv('MAIL_PORT')),
        MAIL_USE_TLS=env_bool(os.getenv('MAIL_USE_TLS')),
        MAIL_USE_SSL=env_bool(os.getenv('MAIL_USE_SSL')),
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME'),
        PASSWORD_RESET_TOKEN_EXPIRATION=int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRATION', 3600)),
        AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID'),
        AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY'),
        AWS_REGION = os.getenv('AWS_REGION'),
        S3_BUCKET = os.getenv('S3_BUCKET'),
        S3_ENDPOINT = os.getenv('S3_ENDPOINT')
    )

    if test_config:
        app.config.from_mapping(test_config)


    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(errors.bp)
    app.register_blueprint(my_recipes.bp)
    app.register_blueprint(planner.bp)
    app.register_blueprint(admin.bp)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Вы не можете получить доступ к данной странице, необходимо сначал войти'

    @app.before_request
    def tmp_file_deleting():
        tmp = session.get('image')
        if not tmp:
            return
        if request.endpoint in ('static', 'werkzeug.debugger', 'my_recipes.create_recipe', 'my_recipes.create_step', 'my_recipes.add_ingredient_in_recipe'):
            return
        delete_object_s3(current_app.config['S3_BUCKET'], tmp)
        session.pop('steps', None)
        session.pop('recipe_data', None)
        session.pop('image', None)
        session.pop('image_mime', None)
        session.pop('image_filename', None)
        session.pop('creating_recipe', None)

    @app.before_request
    def check_user_is_banned():
        if current_user.is_authenticated:
            db = get_db()
            try:
                with db.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT is_banned
                        FROM user_of_app
                        WHERE user_id = %s
                        """,
                        (current_user.id,)
                    )
                    row = cursor.fetchone()
            except (IntegrityError, DatabaseError):
                flash("Ошибка", 'danger')
                return
            if row:
                if row['is_banned']:
                    logout_user()
                    flash("Ваша учётная запись была заблокирована", 'danger')
                    return redirect(url_for('auth.login'))

    def inject_logo_url():
        try:
            logo_url = generate_s3_url(
                current_app.config['S3_BUCKET'],
                'logoforproject.png',
                expires_in=3600,
                public=False
            )
        except Exception:
            logo_url = None

        return dict(logo_url=logo_url)

    app.context_processor(inject_logo_url)

    return app
