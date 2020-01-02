# import os
# from threading import Thread
# from .decorators import matooke
from app import mail
from flask_mail import Message
from flask import current_app

# def send_async_email(app, msg):
#     with app.app_context():
#         mail.send(msg)


def send_email(to, subject, template):
    # msg = Message(subject, sender=sender, recipients=recipients)
    # msg.body = text_body
    # msg.html = html_body
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
    )
    # Thread(target=send_async_email,
    #        args=(current_app._get_current_object(), msg)).start()
    mail.send(msg)

# @matooke
# def send_async_email(app, msg):
#     with app.app_context():
#         mail.send(msg)


# def send_email(subject, sender, recipients, text_body, html_body):
#     msg = Message(
#         subject,
#         sender=sender, recipients=recipients)
#     # msg.body = text_body
#     # msg.html = html_body
#     send_async_email(app, msg)

# def send_email(to, subject, template):
#     msg = Message(
#         subject,
#         recipients=[to],
#         html=template,
#         sender=current_app.config["MAIL_DEFAULT_SENDER"],
#     )
#     # mail.send(msg)
#     send_async_email(app, msg)
