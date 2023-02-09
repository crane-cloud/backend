from flask import render_template
from .email import send_email


def send_user_to_project_notification( email, name, app, template, subject, date, project_name, email_role, success):
    html = render_template(template, 
                            email=email, 
                            name=name, 
                            date= date,
                            project_name = project_name,
                            email_role = email_role,
                            success=success)
    subject = subject
    send_email(email, subject, html, email, app)