from psycopg2 import IntegrityError, DatabaseError

from app.forms.add_to_planner_form import AddToPlannerForm
from app.forms.delete_form import DeleteForm

from flask import Blueprint, render_template, session, flash, current_app, request

from app.forms.search_form import SearchForm
from app.my_recipes.utils import delete_file
from db.db import get_db

bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    db = get_db()
    add_to_planner_form = AddToPlannerForm()
    delete_form = DeleteForm()
    search_form = SearchForm(request.args)

    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_type_id, recipe_type_name
                FROM recipe_type
                ORDER BY recipe_type_name
                """
            )
            data_recipe_types = cursor.fetchall()

            cursor.execute(
                """
                SELECT ingredient_id, name
                FROM ingredient
                ORDER BY name
                """
            )
            data_ingredients = cursor.fetchall()

            cursor.execute(
                """
                SELECT category_id, name
                FROM category
                ORDER BY name
                """
            )
            data_category = cursor.fetchall()
        search_form.recipe_type.choices = [(0, "Все")] + [(r['recipe_type_id'], r['recipe_type_name']) for r in
                                                          data_recipe_types]
        search_form.ingredient.choices = [(0, "Все")] + [(r['ingredient_id'], r['name']) for r in data_ingredients]
        search_form.category.choices = [(0, "Все")] + [(r['category_id'], r['name']) for r in data_category]

        where = ['r.status_of_recipe = %s']
        parametras = ['publicated']

        if search_form.recipe_type.data and int(search_form.recipe_type.data) != 0:
            where.append('r.recipe_type_id = %s')
            parametras.append(int(search_form.recipe_type.data))

        if search_form.ingredient.data and int(search_form.ingredient.data) != 0:
            where.append("""
            EXISTS(SELECT 1 FROM recipe_ingredient AS ri WHERE ri.recipe_id = r.recipe_id AND ri.ingredient_id = %s)
            """)
            parametras.append(int(search_form.ingredient.data))

        if search_form.category.data and int(search_form.category.data) != 0:
            where.append("""
            EXISTS(SELECT 1 FROM recipe_ingredient AS ri JOIN ingredient ON ri.ingredient_id = ingredient.ingredient_id WHERE ri.recipe_id = r.recipe_id AND ingredient.category_id = %s)
            """)
            parametras.append(int(search_form.category.data))

        sql = """
              SELECT recipe_id,
                     title,
                     description,
                     difficulty,
                     creation_date,
                     status_of_recipe,
                     image,
                     image_mime,
                     image_filename
              FROM recipe AS r \
              """
        if where:
            sql += " WHERE " + " AND ".join(where)

        with db.cursor() as cursor:
            cursor.execute(sql, tuple(parametras))
            all_recipes = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при получении данных о рецептах из базы", 'danger')
        all_recipes = []
    return render_template('index/index.html', all_recipes=all_recipes, add_to_planner_form=add_to_planner_form,
                           delete_form=delete_form, search_form=search_form)
