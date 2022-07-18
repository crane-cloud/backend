from flask import render_template
from .email import send_email


def send_invoice(email, name, invoice_id, project_name, total_amount, invoice_date, sender, app, template, subject):
    html = render_template(template, 
                            email=email, 
                            name=name, 
                            invoice_id=invoice_id, 
                            project_name=project_name,
                            total_amount=total_amount,
                            invoice_date=invoice_date)
    subject = subject
    send_email(email, subject, html, sender, app)
