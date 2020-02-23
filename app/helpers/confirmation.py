from flask import render_template
from .email import send_email
from .token import generate_token


def send_verification(email, url, secret_key, password_salt, sender, app):
    token = generate_token(email, secret_key, password_salt)
    verify_url = url + token
    html = render_template("user/verify.html", verify_url=verify_url)
    subject = "please confirm your email"
    send_email(email, subject, html, sender, app)
