DROP TABLE IF EXISTS deps_of_step;
DROP TABLE IF EXISTS recipe_step;
DROP TABLE IF EXISTS recipe_ingredient;
DROP TABLE IF EXISTS ingredient;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS recipe;
DROP TABLE IF EXISTS user_of_app;


CREATE TABLE user_of_app(
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    date_of_registr DATE DEFAULT CURRENT_DATE,
    birthday_date TIMESTAMP,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'usr'
);

CREATE TABLE recipe(
    recipe_id SERIAL PRIMARY KEY,
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recipe_type VARCHAR(50),
    difficulty VARCHAR(50),
    total_time INTEGER,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_of_app(user_id)
);
CREATE TABLE recipe_step(
    recipe_step_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    duration INTEGER NOT NULL,  --в минутах
    type_of VARCHAR(20) CHECK (type_of IN ('passive' , 'active')),
    description TEXT,
    recipe_id INTEGER NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
);

CREATE TABLE deps_of_step (
    id_of_record SERIAL PRIMARY KEY,
    recipe_step_id INTEGER NOT NULL,
    prev_step_id INTEGER NOT NULL,
    FOREIGN KEY (recipe_step_id) REFERENCES recipe_step(recipe_step_id),
    FOREIGN KEY (prev_step_id) REFERENCES recipe_step(recipe_step_id)
);

CREATE TABLE category(
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE ingredient(
    ingredient_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE recipe_ingredient(
    id_of_record SERIAL PRIMARY KEY,
    quantity VARCHAR(50),
    ingredient_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES ingredient(ingredient_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
);

-- Тестовые данные

-- Пользователи
INSERT INTO user_of_app (username, email, password, role)
VALUES
('Иван Иванов', 'ivan@example.com', '12345', 'user'),
('Администратор', 'admin@example.com', 'admin', 'admin');

-- Категории ингредиентов
INSERT INTO category (name, description)
VALUES
('Молочные продукты', 'Все продукты, произведенные из молока'),
('Овощи', 'Свежие овощи'),
('Мясные изделия', 'Мясо и мясные продукты'),
('Зерновые', 'Крупы, макароны, мука'),
('Приправы', 'Соль, специи, соусы');

-- Ингредиенты
INSERT INTO ingredient (name, category_id)
VALUES
('Молоко', 1),
('Сыр', 1),
('Помидор', 2),
('Курица', 3),
('Макароны', 4),
('Соль', 5);

-- Рецепты
INSERT INTO recipe (title, description, recipe_type, difficulty, total_time, user_id)
VALUES
('Паста с соусом', 'Вкусная паста с соусом и сыром', 'основные блюда', 'средняя', 40, 1);

-- Этапы рецепта
INSERT INTO recipe_step (name, description, duration, type_of, recipe_id)
VALUES
('Кипятить воду', 'Налить воду в кастрюлю и довести до кипения', 10, 'passive', 1),
('Замесить тесто', 'Смешать ингредиенты для теста', 15, 'active', 1),
('Сделать соус', 'Приготовить соус из помидоров и приправ', 5, 'active', 1),
('Варить макароны', 'Отварить макароны до готовности', 8, 'passive', 1),
('Запекать', 'Положить всё в форму и запечь', 20, 'passive', 1);

-- Зависимости этапов
INSERT INTO deps_of_step (recipe_step_id, prev_step_id)
VALUES
(4, 1),
(5, 2),
(5, 3);

-- Связь рецепт ↔ ингредиенты
INSERT INTO recipe_ingredient (recipe_id, ingredient_id, quantity)
VALUES
(1, 4, '200 г'),   -- курица
(1, 6, '1 ч.л.'),  -- соль
(1, 5, '150 г');   -- макароны