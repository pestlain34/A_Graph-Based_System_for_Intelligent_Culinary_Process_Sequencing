import psycopg
from flask_login import UserMixin
from db.db import get_db
from app import login_manager
class User(UserMixin):
    def __init__(self, id, username , password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, username, password, role FROM user_of_app WHERE user_id = %s
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        user_id, username, password, role = row['user_id'] , row['username'], row['password'], row['role']
    return User(user_id, username, password, role)





