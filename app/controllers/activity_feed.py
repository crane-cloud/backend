from app.models.app import App
from app.models.tags import Tag
from app.schemas.app import AppSchema
from app.schemas.project import ProjectListSchema
from app.schemas.tags import TagListSchema
from app.schemas.user import UserSchema
from flask import current_app
from flask_restful import Resource, request
from app.models.user import User
from app.models.project import Project
import requests
from flask_jwt_extended import jwt_required, get_jwt_identity


class ActivityFeedView(Resource):
    @jwt_required
    def get(self):
        current_user = User.get_by_id(get_jwt_identity())
        project_schema = ProjectListSchema()
        app_schema = AppSchema()
        tag_schema = TagListSchema()
        user_schema = UserSchema()

        params = {
            'general': True,
            'operations': ['Create', 'Update', 'Delete', 'Follow'],
            'statuses': ['Success'],
            'models': ['Project', 'App', 'Database', 'User']
        }
        user_id = request.args.get('user_id', None)
        if user_id:
            user = User.get_by_id(user_id)
            if not user:
                return dict(status='fail', message='User not found'), 404
            params['user_id'] = user_id

        following = current_user.followed.all()
        if following and not user_id:
            params['user_ids'] = [user.id for user in following]

        tags_followed = current_user.followed_tags
        if tags_followed:
            params['a_tag_ids'] = [tag.tag_id for tag in tags_followed]

        LOGGER_APP_URL = current_app.config.get('LOGGER_APP_URL')
        user_feed = requests.get(
            f"{LOGGER_APP_URL}/api/activities",
            params=params,
            headers={'Authorization': request.headers.get('Authorization')}
        )

        if user_feed.status_code != 200:
            return dict(status='fail', message='Failed to fetch user feed'), 500

        # get project or app details in each item in the feed and return them
        user_feed = user_feed.json()
        user_activities = user_feed.get('data').get('activity')

        if not user_activities:
            return dict(user_feed=user_feed), 200
        for item in user_activities:

            project_is_public = True

            if item['model'] == 'Project' or item['model'] == 'App' or item['model'] == 'Database':

                project = Project.get_by_id(item['a_project_id'])
                project_is_public = project.is_public
                
                if (project.is_public):
                    project_data, _ = project_schema.dump(project)
                    item['project'] = project_schema.dump(project_data)[0]

            tags_list = item.get('a_tag_ids', [])
            if tags_list and len(tags_list) > 0:
                tags = []
                for tag_id in item['a_tag_ids']:
                    tag = Tag.get_by_id(tag_id)
                    tag_data, _ = tag_schema.dump(tag)
                    tags.append(tag_data)
                item['tags'] = tags

            if item['model'] == 'App':
                if project_is_public:
                    app = App.get_by_id(item['a_app_id'])
                    app_data, _ = app_schema.dump(app)
                    item['app'] = app_schema.dump(app_data)[0]

            if item['model'] == 'User' and item['a_user_id'] != None:
                user = User.get_by_id(item['a_user_id'])
                user_data, _ = user_schema.dump(user)
                item['a_user'] = user_schema.dump(user_data)[0]

            elif item['model'] == 'Database':
                pass
        user_feed['data']['activity'] = user_activities

        return dict(user_feed=user_feed), 200
