from marshmallow import Schema, fields


class OrgAdminSchema(Schema):

    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(required=True)