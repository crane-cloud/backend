
import datetime
from flask_jwt_extended import get_jwt_identity
from app.tasks import celery_app
from flask_pymongo import MongoClient
import os
mongo = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
mongo_db = mongo.get_default_database()


def log_activity(model: str, status: str, operation: str, description: str, a_user_id=None, a_db_id=None, a_app_id=None, a_project_id=None, a_cluster_id=None):
    user_id = get_jwt_identity()
    date = str(datetime.datetime.now())
    data = {
        'user_id': user_id,
        'creation_date': date,
        'operation': operation,
        'model': model,
        'status': status,
        'description': description,
        'a_user_id': str(a_user_id) if a_user_id else None,
        'a_db_id': str(a_db_id) if a_db_id else None,
        'a_app_id': str(a_app_id) if a_app_id else None,
        'a_project_id': str(a_project_id) if a_project_id else None,
        'a_cluster_id': str(a_cluster_id) if a_cluster_id else None
    }

    log_user_activity.delay(data)


@celery_app.task(name="log_user_activity")
def log_user_activity(data):
    filtered = {k: v for k, v in data.items() if v is not None}
    try:

        mongo_db['activities'].insert_one(filtered)
        return True
    except Exception as e:
        print(e)
        return False
