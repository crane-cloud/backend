import json
from math import ceil
import os
from types import SimpleNamespace
from app.helpers.activity_logger import log_activity
from app.helpers.kube import disable_project, enable_project
from flask import current_app, render_template
from flask_restful import Resource, request
from flask_bcrypt import Bcrypt
from app.schemas import UserSchema, UserGraphSchema, ActivityLogSchema
from app.models.user import User
from app.models.role import Role
from app.helpers.confirmation import send_verification
from app.helpers.email import send_email
from app.helpers.token import validate_token
from app.helpers.decorators import admin_required
from app.helpers.pagination import paginate
from app.helpers.admin import is_admin
import requests
import secrets
import string
from sqlalchemy import Date, func, column, cast, and_, or_
from app.models import db
from datetime import datetime, timedelta
from app.models.anonymous_users import AnonymousUser
from app.models.project import Project
from app.models.project_users import ProjectUser
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.admin import is_admin, is_authorised_project_user, is_owner_or_admin
from app.models import mongo
from bson.json_util import dumps
from app.models.app import App
from app.helpers.crane_app_logger import logger


class ActivityFeedView(Resource):
    @jwt_required
    def get(self):
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        following = current_user.followed

        params = '?general=True'
        user_id = request.args.get('user_id', None)
        if user_id:
            user = User.get_by_id(user_id)
            if not user:
                return dict(status='fail', message='User not found'), 404
            params = f"{params}&user_id={user_id}"

        LOGGER_APP_URL = current_app.config.get('LOGGER_APP_URL')

        user_feed = requests.get(
            f"{LOGGER_APP_URL}/api/activities{params}",
            headers={'Authorization': request.headers.get('Authorization')}
        )

        if user_feed.status_code != 200:
            return dict(status='fail', message='Failed to fetch user feed'), 500

        return dict(user_feed=user_feed.json()), 200
