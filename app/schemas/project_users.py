from json import load
from marshmallow import Schema, fields

class UserRoleSchema(Schema):
    id = fields.UUID()
    email = fields.String()
    name = fields.String()
class ProjectUserSchema(Schema):

    # id = fields.UUID(dump_only=True)
    id = fields.String(dump_only=True)
    user_id = fields.String(required=True, load_only=True)
    role = fields.String(required=True)
    project_id = fields.String()
    user = fields.Nested(UserRoleSchema, many=False, dump_only=True)
