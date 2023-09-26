from flask import render_template
from .email import send_email
from .token import generate_token


def SendEmail(email , name , status , subject , sender , template , app):
        html = render_template(template,email=email,name=name , status = status)
        send_email(email, subject, html, sender , app)