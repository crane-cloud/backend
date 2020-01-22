from marshmallow import Schema, fields, validate, pre_load


class UserRoleSchema(Schema):

    id = fields.Integer(dump_only=True)

    user_id = fields.Integer(required=True)
    role_id = fields.Integer(required=True)
