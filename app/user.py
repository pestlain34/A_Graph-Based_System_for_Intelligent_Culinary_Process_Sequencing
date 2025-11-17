from flask_login import UserMixin
from db.db import get_db
from app import login_manager


class User(UserMixin):
    def __init__(self, id, username, password, image, image_mime, image_filename, role=None, email=None,
                 birthday_date=None, date_of_registr=None, is_banned=False):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.email = email
        self.birthday_date = birthday_date
        self.date_of_registr = date_of_registr
        self.is_banned = is_banned
        self.image = image
        self.image_mime = image_mime
        self.image_filename = image_filename


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id,
                   username,
                   password,
                   role,
                   email,
                   birthday_date,
                   date_of_registr,
                   is_banned,
                   image,
                   image_mime,
                   image_filename
            FROM user_of_app
            WHERE user_id = %s
            """,
            (user_id,)
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return User(
        id=row['user_id'],
        username=row['username'],
        password=row['password'],
        image=row['image'],
        image_mime=row['image_mime'],
        image_filename=row['image_filename'],
        role=row['role'],
        email=row['email'],
        birthday_date=row['birthday_date'],
        date_of_registr=row['date_of_registr'],
        is_banned=row['is_banned'],
    )
