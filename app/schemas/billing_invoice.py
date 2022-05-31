from marshmallow import Schema, fields, validate
from app.helpers.age_utility import get_item_age


class BillingInvoiceSchema(Schema):

    id = fields.String(dump_only=True)

    project_id = fields.String(required=True, error_message={
        "required": "project_id is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='project_id should be a valid string'
            ),
    ])

    total_amount = fields.Int()
    date_cashed = fields.Date(dump_only=True, required=False)
    is_cashed = fields.Boolean(required=False)
    age = fields.Method("get_age", dump_only=True)
    date_created = fields.Date(dump_only=True)

    def get_age(self, obj):
        return get_item_age(obj.date_cashed)
