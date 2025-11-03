from flask import Blueprint, session, redirect, render_template, request, url_for, flash
from flask_login import login_required
from psycopg2 import DatabaseError, IntegrityError

from app.forms.add_to_planner_form import AddToPlannerForm
from db import db

bp = Blueprint('planner', __name__, url_prefix='/planner')


@bp.route('/add_to_planner/<int:recipe_id>', methods=['POST'])
@login_required
def add_to_planner(recipe_id):
    form = AddToPlannerForm()
    if not form.validate_on_submit():
        flash("Ошбика при добавлении",'danger')
        return redirect(url_for('index.index'))
    if 'recipes_in_planner' not in session:
        session['recipes_in_planner'] = []
    recipes_in_planner = session.get('recipes_in_planner', [])
    if recipe_id in recipes_in_planner:
        flash("Рецепт уже в планировщике", 'info')
        return redirect(url_for('index.index'))
    recipes_in_planner.append(recipe_id)
    session['recipes_in_planner'] = recipes_in_planner
    flash("Рецепт добавлен в планировщик",'success')
    return redirect(url_for('index.index'))
