from app import mail
from flask_mail import Message
from flask import current_app


def send_email(to, subject, template):

    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)

#     # msg.body = text_body
#     # msg.html = html_body
