from app.schemas.project import ProjectIndexSchema
from app.schemas.project_users import UserRoleSchema
from marshmallow import Schema, fields
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

    def get_projects_count(self, obj):
        return len(obj.projects)


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
