from flask import render_template
from .email import send_email
from flask import Flask, request


def send_inactive_notification_to_user( email, name, app, template, subject, date, success):
    client_base_url = f'https://{request.host}'
    html = render_template(template,
                            email=email,
                            client_base_url=client_base_url,
                            name=name, 
                            date= date,
                            success=success)
    subject = subject
    send_email(email, subject, html, email, app)