from app.helpers.invoice_notification import send_invoice, send_sync_invoice

from app.tasks import celery
# from flask import current_app
# from server import app

# current_app = app.app_context()
# print(dir(celery))
# current_app = "celery.app.app_context()"


@celery.task(name='celery_tasks.send_all_invoice_notifications')
def send_invoice_notification(email, name, invoice_id, project_name, total_amount,
                              invoice_date, sender, template,
                              subject):

    # send message
    send_sync_invoice(
        email,
        name,
        invoice_id,
        project_name,
        total_amount,
        invoice_date,
        sender,
        template,
        subject,
    )
