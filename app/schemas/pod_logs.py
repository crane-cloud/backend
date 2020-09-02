from marshmallow import Schema, fields, validate


class PodsLogsSchema(Schema):

    tail_lines = fields.Integer()
    since_seconds = fields.Integer()
    timestamps = fields.Boolean()
