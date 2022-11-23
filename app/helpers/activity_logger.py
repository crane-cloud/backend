
import datetime
from flask_jwt_extended import get_jwt_identity
from app.models import mongo

# Funtion to save activities to mongo db
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
    filtered = {k: v for k, v in data.items() if v is not None }
    try:
        mongo.db['activities'].insert_one(filtered)
        return True
    except Exception:
        return False

