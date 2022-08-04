# from server import celery
from app.tasks import celery


@celery.task(name='celery_tasks.hello')
def hello():
    return 'Hello'
