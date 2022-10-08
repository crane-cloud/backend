from marshmallow import Schema, fields, validate, pre_load


class CreditSchema(Schema):

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(required=True, error_message={
    "required": "user_id is required"})
    amount = fields.Int(required=True, error_message={
    "required": "amount is required"})

