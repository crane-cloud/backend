from json import load
from marshmallow import Schema, fields,validate

class UserRoleSchema(Schema):
    id = fields.UUID()
    email = fields.String()
    name = fields.String()

class UserIndexSchema(Schema):
    id = fields.Method("get_id", dump_only=True)
    email = fields.Method("get_email", dump_only=True)
    name = fields.Method("get_name", dump_only=True)
    def get_id(self, obj):
        return str(obj.user.id)
    def get_email(self, obj):
        return obj.user.email
    def get_name(self, obj):
        return obj.user.name
class ProjectUserSchema(Schema):

    # id = fields.UUID(dump_only=True)
    id = fields.String(dump_only=True)
    email = fields.String(required=True, load_only=True)
    role = fields.String(required=True, validate=[
            validate.OneOf(["owner", "admin", "member"],
                           error='role should either be owner, admin or member'
                           ),
        ])
    project_id = fields.String()
    user = fields.Nested(UserRoleSchema, many=False, dump_only=True)
    accepted_collaboration_invite = fields.Boolean()


class ProjectFollowerSchema(Schema):
    user = fields.Nested(UserRoleSchema, many=False, dump_only=True)