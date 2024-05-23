
import datetime
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.tasks import celery_app
from flask_pymongo import MongoClient
import os
import requests
import json
from app.helpers.crane_app_logger import logger
from flask import current_app


def log_activity(model: str, status: str, operation: str, description: str, a_user_id=None, a_db_id=None, a_app_id=None, a_project_id=None, a_cluster_id=None):
    LOGGER_APP_URL = current_app.config.get('LOGGER_APP_URL')
    if not LOGGER_APP_URL:
        return

    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        user_email = user.email if user else None
        user_name = user.name if user else None
        date = str(datetime.datetime.now())
        data = {
            'user_id': user_id,
            'user_email': user_email,
            'user_name': user_name,
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

        result = requests.post(
            f"{LOGGER_APP_URL}/api/activities", json=data)
        log = result.json()
        logger.info(f"Logging activity: {log['message']}")
    except Exception as e:
        logger.error(f"Error logging activity")
        pass

    # log_user_activity.delay(data)
