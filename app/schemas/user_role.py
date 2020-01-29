from marshmallow import Schema, fields


class UserRoleSchema(Schema):

    id = fields.Integer(dump_only=True)

    user_id = fields.Integer(required=True)
    role_id = fields.Integer(required=True)
