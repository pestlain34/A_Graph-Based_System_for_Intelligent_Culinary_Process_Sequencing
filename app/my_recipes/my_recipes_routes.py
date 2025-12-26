import mimetypes
from collections import defaultdict
from uuid import uuid4
from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app, request
from flask_login import login_required, current_user
from psycopg2 import IntegrityError, DatabaseError
from werkzeug.utils import secure_filename
from app.forms.add_to_planner_form import AddToPlannerForm
from app.forms.create_step import CreateStep_form
from app.forms.delete_form import DeleteForm
from app.forms.ingredients_form import IngredientForm
from app.forms.main_data_of_recipe import Main_data_of_recipe_form
from app.forms.publicate_form import PublicateForm
from app.forms.update_recipe_main_form import Main_data_of_recipe_form_update
from app.services.utils import make_s3_key, upload_fileobj_to_s3, copy_object_s3, delete_object_s3, generate_s3_url
from db.db import get_db

bp = Blueprint('my_recipes', __name__, url_prefix='/my_recipes')


@bp.route('/show_recipes')
@login_required
def show_recipes():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_id,
                       title,
                       description,
                       difficulty,
                       creation_date,
                       status_of_recipe,
                       image
                FROM recipe
                WHERE user_id = %s
                ORDER BY creation_date DESC
                """,
                (current_user.id,)
            )
            recipes = cursor.fetchall()
    except (DatabaseError, IntegrityError):
        flash("Произошла ошибка, при показе твоих рецептов", 'danger')
        recipes = []
    bucket = current_app.config['S3_BUCKET']
    for r in recipes:
        key = r.get('image')
        if key and bucket:
            r['image_url'] = generate_s3_url(bucket, key, expires_in=3600, public=False)
    delete_form = DeleteForm()
    add_to_planner_form = AddToPlannerForm()
    publicate_form = PublicateForm()
    return render_template("my_recipes/show_recipes.html", recipes=recipes, delete_form=delete_form,
                           add_to_planner_form=add_to_planner_form, publicate_form=publicate_form)


@bp.route('/create_recipe', methods=['GET', 'POST'])
@login_required
def create_recipe():
    form = Main_data_of_recipe_form()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_type_id, recipe_type_name
                FROM recipe_type
                ORDER BY recipe_type_name
                """
            )
            rows = cursor.fetchall()


    except (DatabaseError, IntegrityError):
        flash("Ошибка при создании рецепта", 'danger')
        return render_template('my_recipes/create_recipe.html', form=form)

    form.recipe_type.choices = [(row['recipe_type_id'], row['recipe_type_name']) for row in rows]

    if form.validate_on_submit():
        session['recipe_data'] = {
            'title': form.title.data,
            'description': form.description.data,
            'recipe_type_id': form.recipe_type.data,
            'difficulty': form.difficulty.data,
            'user_id': current_user.id,
            'status_of_recipe': 'not_publicated',
            'image_path': None,
        }
        f = form.image.data
        if f:
            bucket = current_app.config['S3_BUCKET']
            key = make_s3_key('tmp', getattr(f, 'filename', 'upload'))
            content_type = f.mimetype or mimetypes.guess_type(f)[0]
            success = upload_fileobj_to_s3(f.stream, bucket, key, content_type=content_type, public=False)
            if success:
                session['image'] = key
                session['image_mime'] = content_type
                session['image_filename'] = secure_filename(f.filename or '')
            else:
                flash("Не удалось загрузить фото", 'danger')
                return render_template('my_recipes/create_recipe.html', form=form)
        session['steps'] = []
        session['ingredients'] = []
        session['creating_recipe'] = True
        return redirect(url_for('my_recipes.add_ingredient_in_recipe'))
    return render_template('my_recipes/create_recipe.html', form=form)


@bp.route('/add_ingredient_in_recipe', methods=['GET', 'POST'])
@login_required
def add_ingredient_in_recipe():
    if 'ingredients' not in session:
        session['ingredients'] = []
    if 'recipe_data' not in session:
        flash("Сначала вам нужно заполнить сведения о рецепте")
        return redirect(url_for('my_recipes.create_recipe'))
    form = IngredientForm()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT ingredient_id, name
                FROM ingredient
                ORDER BY name
                """
            ),
            ingredients_row = cursor.fetchall()
    except (DatabaseError, IntegrityError):
        flash("Ошибка при добавлении ингредиента", 'danger')
        return render_template('add_ingredient_in_recipe.html', form=form)

    form.ingredient.choices = [(row['ingredient_id'], row['name']) for row in ingredients_row]
    ingredients = session.get('ingredients', [])
    if form.validate_on_submit():
        ingredient_data = {
            'quantity': form.amount.data,
            'ingredient_id': form.ingredient.data,
            'edin_izmer': form.edin_izmer.data
        }
        ingredients.append(ingredient_data)
        session['ingredients'] = ingredients

        if form.add_another_ingredient.data:
            flash("Ингредиент добавлен", 'success')
            return redirect(url_for("my_recipes.add_ingredient_in_recipe"))
        if form.go_next.data:
            return redirect(url_for('my_recipes.create_step'))
    return render_template('my_recipes/add_ingredient_in_recipe.html', form=form)


@bp.route('/create_step', methods=['GET', 'POST'])
@login_required
def create_step():
    if 'steps' not in session:
        session['steps'] = []
    if 'recipe_data' not in session:
        flash("Сначала вам нужно заполнить сведения о рецепте")
        return redirect(url_for('my_recipes.create_recipe'))
    form = CreateStep_form()
    steps = session.get('steps', [])
    form.prev_steps.choices = [(i, step['name']) for i, step in enumerate(steps)]
    if form.validate_on_submit():
        step_data = {
            'name': form.name.data,
            'duration': form.duration.data,
            'type_of': form.type_of.data,
            'description': form.description.data,
            'prev_steps': list(map(int, form.prev_steps.data)) if form.prev_steps.data else []
        }
        steps.append(step_data)
        session['steps'] = steps

        if form.add_another_step.data:
            flash('Этап добавлен', 'success')
            return redirect(url_for('my_recipes.create_step'))

        if form.end_recipe.data:
            db = get_db()
            recipe_data = session.get('recipe_data', {})
            steps_data = session.get('steps', [])
            ingredients_data = session.get('ingredients', [])
            try:
                with db.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO recipe (difficulty, title, description, user_id, recipe_type_id, status_of_recipe,
                                            image)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING recipe_id
                        """,
                        (recipe_data['difficulty'], recipe_data['title'], recipe_data['description'],
                         recipe_data['user_id'], recipe_data['recipe_type_id'], recipe_data['status_of_recipe'],
                         session['image'])
                    )
                    row = cursor.fetchone()
                    recipe_id = row['recipe_id']
                    bucket = current_app.config['S3_BUCKET']
                    tmp_key = session.get('image')
                    perm_key = None
                    if tmp_key:
                        filename = session.get('image_filename') or tmp_key.split('/')[-1]
                        perm_key = f"recipes/{recipe_id}/{uuid4().hex}_{secure_filename(filename)}"
                        copied = copy_object_s3(bucket, tmp_key, bucket, perm_key)
                        if copied:
                            delete_object_s3(bucket, tmp_key)
                            session['image'] = perm_key
                        if perm_key:
                            cursor.execute(
                                """
                                UPDATE recipe
                                SET image = %s
                                WHERE recipe_id = %s
                                """,
                                (perm_key, recipe_id)
                            )
                    for ingredient in ingredients_data:
                        cursor.execute(
                            """
                            INSERT INTO recipe_ingredient (quantity, ingredient_id, edin_izmer, recipe_id)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (ingredient['quantity'], ingredient['ingredient_id'], ingredient['edin_izmer'], recipe_id)
                        )

                    index_to_dbid = {}
                    for idx, s in enumerate(steps_data):
                        cursor.execute(
                            """
                            INSERT INTO recipe_step (name, duration, type_of, description, recipe_id)
                            VALUES (%s, %s, %s, %s, %s) RETURNING recipe_step_id
                            """,
                            (s['name'], s['duration'], s['type_of'], s['description'], recipe_id)
                        )
                        row2 = cursor.fetchone()
                        index_to_dbid[idx] = row2['recipe_step_id']

                    for idx, s in enumerate(steps_data):
                        cur_db_id = index_to_dbid[idx]
                        for prev_index in s.get('prev_steps', []):
                            prev_db_id = index_to_dbid.get(prev_index)
                            if prev_db_id:
                                cursor.execute(
                                    """
                                    INSERT INTO deps_of_step (recipe_step_id, prev_step_id)
                                    VALUES (%s, %s)
                                    """,
                                    (cur_db_id, prev_db_id)
                                )
                db.commit()

            except (DatabaseError, IntegrityError):
                db.rollback()
                flash('Ошибка при сохранении рецепта в базу данных, попробуйте еще раз')
                return render_template('my_recipes/create_step.html', form=form)

            session.pop('steps', None)
            session.pop('recipe_data', None)
            session.pop('ingredients', None)
            session.pop('image', None)
            session.pop('image_mime', None)
            session.pop('image_filename', None)
            session.pop('creating_recipe', None)
            flash('Рецепт успешно создан', 'success')
            return redirect(url_for('my_recipes.view_recipe', recipe_id=recipe_id))

    return render_template('my_recipes/create_step.html', form=form)


@bp.route('/view_recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT difficulty, title, description, user_id, recipe_type_id
                FROM recipe
                WHERE recipe_id = %s
                """,
                (recipe_id,)
            )
            recipe = cursor.fetchone()

            if recipe is None:
                flash("Такого рецепта нет в базе рецептов", 'danger')
                return render_template('404.html'), 404

            cursor.execute(
                """
                SELECT recipe_step_id, name, duration, type_of, description, recipe_id
                FROM recipe_step
                WHERE recipe_id = %s
                ORDER BY recipe_step_id
                """,
                (recipe_id,)
            )
            steps = cursor.fetchall()

            cursor.execute(
                """
                SELECT recipe_step_id, prev_step_id
                FROM deps_of_step
                WHERE recipe_step_id IN (SELECT recipe_step_id
                                         FROM recipe_step
                                         WHERE recipe_id = %s)
                """,
                (recipe_id,)
            )
            deps = cursor.fetchall()
            cursor.execute(
                """
                SELECT ri.ingredient_id, ri.quantity, ri.recipe_id, ri.edin_izmer, i.name
                FROM recipe_ingredient AS ri
                         JOIN ingredient AS i ON i.ingredient_id = ri.ingredient_id
                WHERE ri.recipe_id = %s
                """,
                (recipe_id,)
            )
            ingredients_data = cursor.fetchall()

    except (DatabaseError, IntegrityError):
        db.rollback()
        flash("Ошибка сервера при загрузке рецепта", 'danger')
        return render_template("error.html"), 500

    deps_map = defaultdict(list)
    for d in deps:
        deps_map[d['recipe_step_id']].append(d['prev_step_id'])

    id_to_index = {step['recipe_step_id']: i + 1 for i, step in enumerate(steps)}
    id_to_name = {step['recipe_step_id']: step['name'] for step in steps}
    for step in steps:
        previd_list = deps_map.get(step['recipe_step_id'], [])
        step['prev_numbers'] = [id_to_index[previd] for previd in previd_list if previd in id_to_index]
        step['prev_names'] = [id_to_name[previd] for previd in previd_list if previd in id_to_name]

    total_time = sum(s['duration'] for s in steps)
    return render_template("recipe/view_recipe.html", recipe=recipe, steps=steps, total_time=total_time,
                           ingredients=ingredients_data)


@bp.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, image
                FROM recipe
                WHERE recipe_id = %s
                """,
                (recipe_id,)
            )
            row = cursor.fetchone()
            if row is None:
                flash("Рецепт не найден", 'danger')
                return redirect(url_for('my_recipes.show_recipes'))
            curid = row['user_id']
            if curid != current_user.id:
                flash("У вас нет прав удалять этот рецепт", 'danger')
                return redirect(url_for('my_recipes.show_recipes'))
            relpath = row['image']
            delete_object_s3(current_app.config['S3_BUCKET'], relpath)
            cursor.execute(
                """
                DELETE
                FROM recipe
                WHERE recipe_id = %s
                """,
                (recipe_id,)
            )
            cursor.execute(
                """
                DELETE
                FROM recipe_ingredient
                WHERE recipe_id = %s
                """,
                (recipe_id,)
            )
        db.commit()
    except (IntegrityError, DatabaseError):
        db.rollback()
        flash("Ошибка при удалении рецепта", 'danger')
        return redirect(url_for('my_recipes.show_recipes'))

    flash("Успешное удаление рецепта", 'success')
    return redirect(url_for('my_recipes.show_recipes'))


@bp.route('/publicate_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def publicate_recipe(recipe_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recipe
                SET status_of_recipe = %s
                WHERE recipe_id = %s
                """,
                ("under_consideration", recipe_id,)
            )
        db.commit()

    except (IntegrityError, DatabaseError):
        flash("Ошибка при отправке рецепта на публикацию", 'danger')
        return redirect(url_for('my_recipes.show_recipes'))

    flash("Успешная отправка рецепта на публикацию", 'success')
    return redirect(url_for('my_recipes.show_recipes'))


@bp.route('/update_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
    form = Main_data_of_recipe_form_update()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipe_type_id, recipe_type_name
                FROM recipe_type
                ORDER BY recipe_type_name
                """
            )
            recipe_type_data = cursor.fetchall()
        form.recipe_type.choices = [(r['recipe_type_id'], r['recipe_type_name']) for r in recipe_type_data]
    except (DatabaseError, IntegrityError):
        flash("Ошибка изменения рецепта", 'danger')
        return redirect(url_for('my_recipes.show_recipes'))
    if request.method == 'GET':
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT title, description, recipe_type_id, difficulty, image
                    FROM recipe
                    WHERE recipe_id = %s
                    """,
                    (recipe_id,)
                )
                recipe_data = cursor.fetchone()

            if not recipe_data:
                flash("Рецепт не найден", "danger")
                return redirect(url_for('my_recipes.show_recipes'))
            rt_id = recipe_data['recipe_type_id']
            form.title.data = recipe_data['title']
            form.description.data = recipe_data['description']
            form.difficulty.data = recipe_data['difficulty']
            form.recipe_type.data = int(rt_id) if rt_id is not None else None

        except (DatabaseError, IntegrityError):
            flash("Ошибка изменения рецепта", 'danger')
            return redirect(url_for('my_recipes.show_recipes'))
    if form.validate_on_submit():
        f = form.image.data
        new_key = None
        old_key = None
        if f:
            bucket = current_app.config['S3_BUCKET']
            filename_safe = secure_filename(getattr(f, 'filename', '') or 'image')
            content_type = f.mimetype or (mimetypes.guess_type(filename_safe)[0] if filename_safe else None)
            new_key = make_s3_key('recipes', filename_safe)
            ok = upload_fileobj_to_s3(f.stream, bucket, new_key, content_type=content_type, public=False)
            if not ok:
                flash("Не удалось загрузить изображение", 'danger')
                return redirect(url_for('my_recipes.show_recipes'))
        try:
            with db.cursor() as cursor:
                if new_key:
                    cursor.execute(
                        """
                        SELECT image
                        FROM recipe
                        WHERE recipe_id = %s
                        """,
                        (recipe_id,)
                    )
                    old_key_data = cursor.fetchone()

                    cursor.execute(
                        """
                        UPDATE recipe
                        SET title          = %s,
                            description    = %s,
                            recipe_type_id    = %s,
                            difficulty     = %s,
                            image          = %s,
                            status_of_recipe = %s
                        WHERE recipe_id = %s
                        """,
                        (form.title.data, form.description.data, form.recipe_type.data, form.difficulty.data,
                         new_key,'under_consideration',recipe_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE recipe
                        SET title       = %s,
                            description = %s,
                            recipe_type_id = %s,
                            difficulty  = %s,
                            status_of_recipe = %s
                        WHERE recipe_id = %s
                        """,
                        (form.title.data, form.description.data, form.recipe_type.data, form.difficulty.data, 'under_consideration', recipe_id)
                    )
            db.commit()

        except (DatabaseError, IntegrityError):
            db.rollback()
            if new_key:
                delete_object_s3(current_app.config['S3_BUCKET'], new_key)
            flash("Ошибка при изменении данных", 'danger')
            return redirect(url_for('my_recipes.show_recipes'))
        if new_key and old_key and old_key != new_key:
            delete_object_s3(current_app.config['S3_BUCKET'], old_key_data['image'])
        flash("Данные рецепта успешно обновлены", 'success')
        return redirect(url_for('my_recipes.view_recipe', recipe_id=recipe_id))
    return render_template("my_recipes/update_recipe.html", form= form, recipe_id=recipe_id, title = "Редактирование рецепта")
