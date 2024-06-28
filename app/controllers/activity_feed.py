from flask import current_app
from flask_restful import Resource, request
from app.models.user import User
import requests
from flask_jwt_extended import jwt_required, get_jwt_identity


class ActivityFeedView(Resource):
    @jwt_required
    def get(self):
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)

        params = {
            'general': True,
            'operations': ['Create', 'Update', 'Delete'],
            'statuses': ['Success'],
            'models': ['Project', 'App', 'Database', ]
        }
        user_id = request.args.get('user_id', None)
        if user_id:
            user = User.get_by_id(user_id)
            if not user:
                return dict(status='fail', message='User not found'), 404
            params['user_id'] = user_id

        following = current_user.followed
        if following:
            params['user_ids'] = [user.id for user in following]

        LOGGER_APP_URL = current_app.config.get('LOGGER_APP_URL')

        user_feed = requests.get(
            f"{LOGGER_APP_URL}/api/activities",
            params=params,
            headers={'Authorization': request.headers.get('Authorization')}
        )

        if user_feed.status_code != 200:
            return dict(status='fail', message='Failed to fetch user feed'), 500

        return dict(user_feed=user_feed.json()), 200
