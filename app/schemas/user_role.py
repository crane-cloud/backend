from marshmallow import Schema, fields


class UserRoleSchema(Schema):

    id = fields.UUID(dump_only=True)
    role_id = fields.String(required=True)
