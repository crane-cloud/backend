from flask import render_template
from .email import send_email


def send_invoice(email, name, sender, app, template, subject):
    html = render_template(template, email=email, name=name)
    subject = subject
    send_email(email, subject, html, sender, app)
