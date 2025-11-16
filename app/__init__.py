import os
from flask import Flask, flash, redirect, url_for, session, current_app, request
from flask.cli import load_dotenv
from flask_login import current_user, logout_user
from psycopg2 import IntegrityError, DatabaseError

from db.db import get_db
from instance.config import basedir
from .extensions import login_manager, bootstrap, mail
from db import db
from . import auth
from . import index
from . import profile
from . import errors
from . import my_recipes
from . import planner
from . import admin
from .my_recipes.utils import delete_file


def env_bool(name):
    if name == "True":
        return True
    return False




load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=(
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_SERVER')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )

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
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'image', 'recipes')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)

    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)

    except OSError:
        pass

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
        if request.endpoint in ('static', 'werkzeug.debugger', 'my_recipes.create_recipe', 'my_recipes.create_step'):
            return
        delete_file(current_app.static_folder, tmp)
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


    return app
