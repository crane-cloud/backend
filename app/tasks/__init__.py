import os
from celery import Celery
from flask import current_app

from ..helpers.invoice_notification import send_invoice
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
celery = Celery(__name__, broker=redis_url,
                backend=redis_url, include=['app.tasks'])


def update_celery(app):
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


@celery.task(name="send_async_remainder_email")
def send_async_email(email,
                     name,
                     invoice_id,
                     project_name,
                     total_amount,
                     invoice_date,
                     sender,
                     template,
                     subject):

    # send message
    send_invoice(
        email,
        name,
        invoice_id,
        project_name,
        total_amount,
        invoice_date,
        sender,
        current_app._get_current_object(),
        template,
        subject
    )


@celery.task
def hello():
    print('hello')
    return 'hello'
