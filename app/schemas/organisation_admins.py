from marshmallow import Schema, fields


class OrgAdminSchema(Schema):

    id = fields.UUID(dump_only=True)
    user_id = fields.String(required=True)