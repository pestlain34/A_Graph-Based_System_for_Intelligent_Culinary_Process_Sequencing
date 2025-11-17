from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for, render_template

from app import mail


def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_password_reset_token(user_id):
    s = get_serializer()
    return s.dumps({'user_id': user_id}, salt="password-reset-token")


def verify_password_reset_token(token):
    s = get_serializer()
    max_time = current_app.config.get("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 3600)
    try:
        data = s.loads(token, salt="password-reset-token", max_age=max_time)

    except Exception:
        return None
    return data.get('user_id')


def send_password_reset_email(to_email, token):
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    subject = 'Сброс пароля'
    text_body = render_template('auth/reset_password.txt', reset_url=reset_url)
    html_body = render_template('auth/reset_password.html', reset_url=reset_url)
    msg = Message(subject=subject, recipients=[to_email], body=text_body, html=html_body)
    mail.send(msg)
