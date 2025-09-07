from app.models.tags import ProjectTag
from marshmallow import Schema, fields, validate
from app.helpers.age_utility import get_item_age
from app.models.app import App
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.models.project_users import ProjectFollowers, ProjectUser


class ProjectMiniListSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.String()
    alias = fields.String()
    disabled = fields.Boolean()
    description = fields.String()


class ProjectIndexSchema(Schema):
    id = fields.Method("get_id", dump_only=True)
    name = fields.Method("get_name", dump_only=True)
    description = fields.Method("get_description", dump_only=True)

    def get_id(self, obj):
        return str(obj.project.id)

    def get_name(self, obj):
        return obj.project.name

    def get_description(self, obj):
        return obj.project.description


class ProjectListSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.String()
    description = fields.String()
    tags = fields.Nested("TagsProjectsSchema", many=True, dump_only=True)
    supports_ml = fields.Method("get_supports_ml", dump_only=True)

    def get_supports_ml(self, obj):
        return obj.cluster.supports_ml


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
    followers_count = fields.Method("get_followers_count", dump_only=True)
    members_count = fields.Method("get_members_count", dump_only=True)
    is_following = fields.Method("get_is_following", dump_only=True)
    is_pinned = fields.Method("get_pinned_status", dump_only=True)
    is_public = fields.Boolean()
    tags = fields.Nested("TagsProjectsSchema", many=True, dump_only=True)
    tags_add = fields.List(fields.String, load_only=True)
    tags_remove = fields.List(fields.String, load_only=True)
    supports_ml = fields.Method("get_supports_ml", dump_only=True)
    tags_count = fields.Method("get_tags_count", dump_only=True) 

    def get_is_following(self, obj):
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        return obj.is_followed_by(current_user)

    def get_age(self, obj):
        return get_item_age(obj.date_created)

    def get_apps_count(self, obj):
        return App.count(project_id=obj.id)

    def get_prometheus_url(self, obj):
        return obj.cluster.prometheus_url

    def get_followers_count(self, obj):
        return ProjectFollowers.count(project_id=obj.id)
    
    def get_members_count(self, obj):
        return ProjectUser.count(project_id=obj.id)

    def get_supports_ml(self, obj):
        return obj.cluster.supports_ml
    
    def get_tags_count(self, obj):
        return ProjectTag.count(project_id=obj.id)
      
    def get_pinned_status(self, obj):
        project_user = ProjectUser.query.filter_by(
            project_id=obj.id,
        ).first()
        return project_user.pinned if project_user else False



class ProjectMigrationSchema(Schema):
    new_cluster_id = fields.String(required=True)
