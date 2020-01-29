from marshmallow import Schema, fields


class OrgMemberSchema(Schema):

    id = fields.Integer(dump_only=True)

    user_id = fields.Integer(required=True)
    organisation_id = fields.Integer(required=True)
