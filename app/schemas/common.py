from marshmallow import Schema, fields


class DisableSchema(Schema):
    disabled_reason = fields.String(required=True)


class BaseSchema(Schema):
    deleted = fields.Boolean(dump_only=True)
    disabled = fields.Boolean(dump_only=True)
    admin_disabled = fields.Boolean(dump_only=True)
    disabled_reason = fields.String(dump_only=True)
    deleted_at = fields.DateTime(dump_only=True)
    disabled_at = fields.DateTime(dump_only=True)
    enabled_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
