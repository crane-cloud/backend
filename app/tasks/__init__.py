import os
import json
from celery import Celery , shared_task, states
from flask import current_app
from app.schemas.credit_assignments import CreditAssignmentSchema
from ..helpers.invoice_notification import send_invoice
from datetime import date, datetime
from app.models.credits import Credit
from app.schemas import CreditAssignmentSchema
from app.models.credit_assignments import CreditAssignment
from sqlalchemy import extract, func, and_
from app.models import db
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import SQLAlchemy
from celery.schedules import crontab
from dateutil.relativedelta import *
from app.models.user import User

from ..helpers.invoice_notification import send_invoice
from ..helpers.credit_expiration_notification import send_credit_expiration_notification

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



@celery.on_after_configure.connect
def setup_periodic_tasks(**kwargs):
    # Calls updateScheduler everyday at midnight
    celery.add_periodic_task(crontab(minute=0, hour=0), updateScheduler.s(), name='check credits expiry')
    celery.add_periodic_task(crontab(minute=0, hour=0), sendExpirationNotification.s(), name='send credits expiry notifications')

@celery.task()
def updateScheduler():
    
    app = current_app

    db = SQLAlchemy()

    db.create_all()

    print("Executing task : Checking credit expiry...")
    credit_assignment_schema = CreditAssignmentSchema(many = True)

    todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    
    try:
        sq = db.session.query(CreditAssignment.user_id, func.max(CreditAssignment.expiry_date).label('expiry_date')).group_by(CreditAssignment.user_id).subquery()
        
        
        credit_assignment_records= db.session.query(Credit.user_id, Credit.amount, sq.c.expiry_date).join(sq,and_(Credit.user_id == sq.c.user_id)).filter(extract('month', sq.c.expiry_date) == datetime.today().month,extract('year', sq.c.expiry_date) == datetime.today().year,extract('day', sq.c.expiry_date) == datetime.today().day,
                            Credit.amount!= 0)
            
        print(type(credit_assignment_records))
        credit_assignments_json, errors = credit_assignment_schema.dumps(credit_assignment_records)
        
        arr= json.loads(credit_assignments_json)
        
       
        if len(arr)>0:
            for i in arr:
                # update query
                sql = db.session.query(Credit).filter(Credit.user_id == i['user_id'], Credit.amount == i['amount']).update({Credit.amount:0}, synchronize_session = False)
                db.session.commit()
                
                print(i['amount'])
                print("updated for amount ",i['amount'])
        print(arr)
        print("Credit expiry checks complete!")
    except SQLAlchemyError as e:
        return dict(status='Fail',
                    message='Internal server error'), 500

# celery.update_state(state=states.SUCCESS)
# celery -A server.celery worker -B -l info

@celery.task()
def sendExpirationNotification():

    app = current_app

    db = SQLAlchemy()

    db.create_all()

    print("Executing task : Sendiing credit expiry notifications...")
    credit_assignment_schema = CreditAssignmentSchema(many = True)

    notification_datetime = datetime.today() +relativedelta(months=+1)
    
    try:
        sq = db.session.query(CreditAssignment.user_id, func.max(CreditAssignment.expiry_date).label('expiry_date')).group_by(CreditAssignment.user_id).subquery()

        # look for credits that expire from a month from now
        credit_assignment_records= db.session.query(Credit.user_id, Credit.amount, sq.c.expiry_date).join(sq,and_(Credit.user_id == sq.c.user_id)).filter(extract('month', sq.c.expiry_date) == notification_datetime.month,extract('year', sq.c.expiry_date) == notification_datetime.year,extract('day', sq.c.expiry_date) == notification_datetime.day,
                            Credit.amount!= 0)
       

        credit_assignments_json, errors = credit_assignment_schema.dumps(credit_assignment_records)
        
        arr= json.loads(credit_assignments_json)
        
       
        if len(arr)>0:
            for i in arr:

                #email variables
                user_credit = Credit.find_first(user_id=i['user_id'])
                user = User.get_by_id(i['user_id'])
                sender = user.email
                name = user.name
                template = "user/credit_expiration_notification.html"
                subject = "Promotional Credits Expiration from Crane Cloud Project"
                email =user.email
                amount = user_credit.amount_promotion_credits
                today = notification_datetime
                success = False

                # send email 
                success = True
                send_credit_expiration_notification(
                email,
                name,
                sender,
                current_app._get_current_object(),
                template,
                subject,
                amount,
                today.strftime("%m/%d/%Y"), 
                success
                )
        return 'Expiration notifications sent!'

    except SQLAlchemyError as e:
        return dict(status='Fail',
                    message='Internal server error'), 500

    

@celery.task
def hello():
    print('hello')
    return 'hello'
