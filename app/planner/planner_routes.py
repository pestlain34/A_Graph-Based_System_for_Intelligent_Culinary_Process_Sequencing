from collections import defaultdict
from urllib.parse import urlsplit

from flask import Blueprint, session, redirect, render_template, request, url_for, flash
from flask_login import login_required
from psycopg2 import DatabaseError, IntegrityError

from app.forms.add_to_planner_form import AddToPlannerForm
from app.forms.delete_form import DeleteForm
from app.planner.topologicalsort import Step, schedule_improved
from db.db import get_db

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
        next = request.args.get('next')
        if not next or urlsplit(next).netloc != '':
            next = url_for('index.index')
        return redirect(next)
    recipes_in_planner.append(recipe_id)
    session['recipes_in_planner'] = recipes_in_planner
    flash("Рецепт добавлен в планировщик",'success')
    next = request.args.get('next')
    if not next or urlsplit(next).netloc != '':
        next = url_for('index.index')
    return redirect(next)

@bp.route('/show_recipes_in_planner')
@login_required
def show_recipes_in_planner():
    recipes_in_planner = session.get('recipes_in_planner', [])
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_id, title, description, difficulty, creation_date FROM recipe WHERE recipe_id = ANY(%s) ORDER BY creation_date DESC
                """,
                (recipes_in_planner,)
            )
            rows = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        flash("Ошибка при загрузке данных из базы", 'danger')
        rows = []
    delete_form = DeleteForm()
    return render_template('planner/show_recipes_in_planner.html', rows = rows, delete_form = delete_form)

@bp.route('/delete_from_planner/<int:recipe_id>', methods = ['POST'])
@login_required
def delete_from_planner(recipe_id):
    recipes_in_planner = session.get('recipes_in_planner', [])
    if recipe_id in recipes_in_planner:
        recipes_in_planner.remove(recipe_id)
        session['recipes_in_planner'] = recipes_in_planner
        flash("Успешное удаление рецепта из планировщика",'success')
    else:
        flash("Ошибка, такого рецепта нет в планировщике", 'danger')

    return redirect(url_for('planner.show_recipes_in_planner'))

@bp.route('/start_planner', methods = ['GET', 'POST'])
@login_required
def start_planner():
    recipes_in_planner = session.get('recipes_in_planner', [])
    if not recipes_in_planner:
        flash("Планировщик пуст", 'info')
        return redirect(url_for('planner.show_recipes_in_planner'))

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_step_id, name, duration, type_of, description
                FROM recipe_step
                WHERE recipe_id = ANY (%s)
                """,
                (recipes_in_planner,)
            )
            finded_steps = cursor.fetchall()

            cursor.execute(
                """
                SELECT recipe_step_id, prev_step_id FROM deps_of_step WHERE recipe_step_id IN (SELECT recipe_step_id
                FROM recipe_step WHERE recipe_id = ANY(%s))
                """,
                (recipes_in_planner,)
            )
            dependencies = cursor.fetchall()


    except (DatabaseError, IntegrityError):
        flash("Ошибка при генерации планировшика", 'danger')
        return redirect(url_for('planner.show_recipes_in_planner'))

    steps_by_id = {}

    for step in finded_steps:
        sid, name, duration , type_of = step['recipe_step_id'], step['name'], step['duration'], step['type_of']
        is_active  = True if step['type_of'] == 'active' else False
        step_obj = Step(sid, name, duration, is_active, prev=[])
        step_obj.description = step.get('description', '')
        steps_by_id[sid] = step_obj

    for dep in dependencies:
        child_id = dep['recipe_step_id']
        parent_id = dep['prev_step_id']
        steps_by_id[child_id].prev.append(steps_by_id[parent_id])

    steps = list(steps_by_id.values())
    if not steps:
        flash("Нет шагов для выбранных рецептов", "info")
        return redirect(url_for('planner.show_recipes_in_planner'))
    try:
        plan = schedule_improved(steps)

    except Exception:
        flash("Не удалось составить план", 'danger')
        return redirect(url_for('planner.show_recipes_in_planner'))

    better_plan = []
    id_to_index = {step['recipe_step_id']: i + 1 for i, step in enumerate(finded_steps)}
    id_to_name = {step['recipe_step_id']: step['name'] for step in finded_steps}
    deps_map = defaultdict(list)
    for d in dependencies:
        deps_map[d['recipe_step_id']].append(d['prev_step_id'])
    for el in plan:
        sid = el.get('id')
        name = el.get('name')
        start = el.get('start')
        end = el.get('end')
        type_of = el.get('type_of')

        st = steps_by_id.get(sid)
        previd_list = deps_map.get(sid, [])
        description = getattr(st, 'description', '')
        better_plan.append({
            'sid': sid,
            'name': name,
            'start': start,
            'end': end,
            'type_of': type_of,
            'description': description,
            'previd_list': previd_list,
            'prev_numbers': [id_to_index[previd] for previd in previd_list if previd in id_to_index],
            'prev_names' : [id_to_name[previd] for previd in previd_list if previd in id_to_name]

        })
    total_time = max(item['end'] for item in better_plan)
    return render_template('planner/plan.html', better_plan= better_plan, total_time = total_time)