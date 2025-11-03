import psycopg
from flask_login import UserMixin
from db.db import get_db
from app import login_manager
class User(UserMixin):
    def __init__(self, id, username , password, role= None, email= None, birthday_date= None,date_of_registr=None):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.email = email
        self.birthday_date = birthday_date
        self.date_of_registr = date_of_registr

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, username, password, role, email , birthday_date,date_of_registr FROM user_of_app WHERE user_id = %s
            """,
            (user_id,)
        )
        row = cursor.fetchone()
    if row is None:
        return None
    user_id, username, password, role, email , birthday_date, date_of_registr = row['user_id'] , row['username'], row['password'], row['role'], row['email'], row['birthday_date'], row['date_of_registr']
    return User(user_id, username, password, role, email, birthday_date, date_of_registr)





