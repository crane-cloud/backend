from marshmallow import Schema, fields, validate
from app.helpers.age_utility import get_item_age


class BillingReceiptSchema(Schema):

    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID()
    project_id = fields.String(required=False,
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='project_id should be a valid string'
            ),
    ])
    billing_invoice_id = fields.String(required=False,
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='project_id should be a valid string'
            ),
    ])
    amount = fields.Int()
    name = fields.String(required=False, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    email = fields.Email(required=False)
    transaction_id = fields.Int()

    def get_age(self, obj):
        return get_item_age(obj.date_created)
