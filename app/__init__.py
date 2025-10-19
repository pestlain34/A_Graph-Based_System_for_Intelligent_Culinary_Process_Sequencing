import os
from flask import Flask
from flask.cli import load_dotenv
from .extensions import login_manager, bootstrap
from db import db
from . import auth
from . import index

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=(
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_SERVER')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
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
    app.register_blueprint(auth.bp)
    app.register_blueprint(index.bp)
    login_manager.login_view = 'auth/login'
    login_manager.login_message = 'Вы не можете получить доступ к данной странице, необходимо сначал войти'
    return app
