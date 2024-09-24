from app.schemas.project import ProjectIndexSchema
from app.schemas.project_users import UserRoleSchema
from marshmallow import Schema, fields
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.models.tags import TagFollowers


class TagListSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.String(required=True)
    is_super_tag = fields.Boolean()


class TagSchema(Schema):

    id = fields.UUID(dump_only=True)
    name = fields.String(required=True)
    is_super_tag = fields.Boolean()
    date_created = fields.Date(dump_only=True)
    projects_count = fields.Method("get_projects_count", dump_only=True)
    is_following = fields.Method("get_is_following", dump_only=True)

    def get_projects_count(self, obj):
        return len(obj.projects)

    def get_is_following(self, obj):
        current_user_id = get_jwt_identity()
        tag_id = obj.id
        return TagFollowers.check_exists(user_id=current_user_id, tag_id=tag_id)


class TagsProjectsSchema(TagSchema):
    name = fields.Method("get_name", dump_only=True)
    id = fields.Method("get_id", dump_only=True)
    is_super_tag = fields.Method("get_is_super_tag", dump_only=True)

    def get_id(self, obj):
        return str(obj.tag.id)

    def get_name(self, obj):
        return obj.tag.name

    def get_is_super_tag(self, obj):
        return obj.tag.is_super_tag


class TagsDetailSchema(TagSchema):
    projects = fields.Nested(ProjectIndexSchema, many=True, dump_only=True)


class TagFollowerSchema(Schema):
    user = fields.Nested(UserRoleSchema, many=False, dump_only=True)
