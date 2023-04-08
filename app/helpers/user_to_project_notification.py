from flask import render_template
from .email import send_email
import os
from flask_restful import Resource, request


def send_user_to_project_notification( email, name, app, template, subject, date, project_name, email_role, success):
  
    client_base_url = f'https://{request.host}/register'
    
    html = render_template(template,
                            email=email,
                            client_base_url=client_base_url,
                            name=name, 
                            date= date,
                            project_name = project_name,
                            email_role = email_role,
                            success=success)
    subject = subject
    send_email(email, subject, html, email, app)