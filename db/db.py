import psycopg2
import psycopg2.extras
from flask import current_app, g
import click
import os

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            current_app.config["DATABASE"],
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    return g.db

def close_db(e = None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

try:
    import sqlparse
except Exception:
    sqlparse = None

def init_db():
    db = get_db()
    sql_path = os.path.join(os.path.dirname(__file__), 'generate.sql')

    with open(sql_path, 'rb') as f:
        sql_text = f.read().decode('utf-8')

    if sqlparse:
        statements = [s.strip() for s in sqlparse.split(sql_text) if s.strip()]
    else:
        # fallback: простой фильтр
        parts = [p.strip() for p in sql_text.split(';')]
        statements = [p for p in parts if p and not p.lstrip().startswith('--')]

    try:
        with db.cursor() as cursor:
            for stmt in statements:
                cursor.execute(stmt)
        db.commit()
    except Exception:
        db.rollback()
        raise

@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)