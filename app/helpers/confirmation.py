from flask import render_template
from .email import send_email
from .token import generate_token


def send_verification(email, name, url, secret_key, password_salt, sender, app, template, subject):
    token = generate_token(email, secret_key, password_salt)
    verify_url = url + token
    html = render_template(template, verify_url=verify_url, email=email, name=name)
    subject = subject
    send_email(email, subject, html, sender, app)
