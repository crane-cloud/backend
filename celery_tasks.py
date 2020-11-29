from server import celery

@celery.task(name='celery_tasks.hello')
def hello():
    return 'Hello'
