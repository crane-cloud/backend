from marshmallow import Schema, fields, validate
from app.helpers.age_utility import get_item_age
from app.models.app import App
from flask_jwt_extended import get_jwt_identity
from app.models.user import User


class ProjectListSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.String()
    description = fields.String()


class ProjectSchema(Schema):

    id = fields.UUID(dump_only=True)
    name = fields.String(required=True, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    owner_id = fields.UUID(required=True, error_message={
        "required": "owner_id is required"
    })
    cluster_id = fields.UUID(required=True, error_message={
        "required": "cluster_id is required"
    })
    description = fields.String()
    organisation = fields.String()
    project_type = fields.String()
    alias = fields.String(required=False)
    date_created = fields.Date(dump_only=True)
    age = fields.Method("get_age", dump_only=True)
    apps_count = fields.Method("get_apps_count", dump_only=True)
    disabled = fields.Boolean(dump_only=True)
    admin_disabled = fields.Boolean(dump_only=True)
    prometheus_url = fields.Method("get_prometheus_url", dump_only=True)
    is_following = fields.Method("get_is_following", dump_only=True)
    tags = fields.Nested("TagsProjectsSchema", many=True, dump_only=True)
    tags_add = fields.List(fields.String, load_only=True)
    tags_remove = fields.List(fields.String, load_only=True)

    def get_is_following(self, obj):
        # Assuming current_user is available in the view context
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        return obj.is_followed_by(current_user)

    def get_age(self, obj):
        return get_item_age(obj.date_created)

    def get_apps_count(self, obj):
        return App.count(project_id=obj.id)

    def get_prometheus_url(self, obj):
        return obj.cluster.prometheus_url
