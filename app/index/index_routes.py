from collections import defaultdict

import psycopg2
from flask_login import login_required, current_user
from psycopg2 import IntegrityError, DatabaseError

from app.forms.add_to_planner_form import AddToPlannerForm
from app.forms.delete_form import DeleteForm
from app.forms.main_data_of_recipe import Main_data_of_recipe_form
from app.forms.create_step import CreateStep_form
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from app.my_recipes.utils import delete_file
from app.planner.planner_routes import add_to_planner
from db.db import get_db

bp = Blueprint('index',__name__)

@bp.route('/')
def index():
    tmp = session.pop('image', None)
    if tmp:
        delete_file(current_app.static_folder, tmp)
    session.pop('steps', None)
    session.pop('recipe_data', None)
    add_to_planner_form = AddToPlannerForm()
    delete_form = DeleteForm()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_id, title, description, difficulty, creation_date, status_of_recipe, image,image_mime, image_filename
                FROM recipe
                WHERE status_of_recipe = %s
                ORDER BY creation_date DESC
                """,
                ("publicated",)
            )
            all_recipes = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении данных о рецептах из базы", 'danger')
        all_recipes = []
    return render_template('index/index.html', all_recipes=all_recipes, add_to_planner_form=add_to_planner_form, delete_form=delete_form)
