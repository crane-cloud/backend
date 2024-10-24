from marshmallow import Schema, fields, validate


class AppStateSchema(Schema):
    id = fields.UUID(dump_only=True)
    app = fields.String()
    reason = fields.String()
    message = fields.String()
    status = fields.String(required=True, validate=[
        validate.OneOf(["running", "unknown", "failed"],
                       error='Status should either be running, unknown or failed'
                       ),
    ])
    last_check = fields.Date(dump_only=True)
