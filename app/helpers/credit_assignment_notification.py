from flask import render_template
from .email import send_email


def send_credit_assignment( email, name, sender, app, template, subject, amount,date, success):
    html = render_template(template, 
                            email=email, 
                            name=name, 
                            amount= amount,
                            date= date,
                            success=success)
    subject = subject
    send_email(email, subject, html, sender, app)