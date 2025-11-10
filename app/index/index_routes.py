from collections import defaultdict

import psycopg2
from flask_login import login_required, current_user
from psycopg2 import IntegrityError, DatabaseError

from app.forms.add_to_planner_form import AddToPlannerForm
from app.forms.main_data_of_recipe import Main_data_of_recipe_form
from app.forms.create_step import CreateStep_form
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.planner.planner_routes import add_to_planner
from db.db import get_db

bp = Blueprint('index',__name__)

@bp.route('/')
def index():
    session.pop('steps', None)
    session.pop('recipe_data', None)
    add_to_planner_form = AddToPlannerForm()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_id, title, description, difficulty, creation_date
                FROM recipe
                ORDER BY creation_date DESC
                """
            )
            all_recipes = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении данных о рецептах из базы", 'danger')
        all_recipes = []
    return render_template('index/index.html', all_recipes=all_recipes, add_to_planner_form=add_to_planner_form)
