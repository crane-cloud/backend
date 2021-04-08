from marshmallow import Schema, fields, validate, pre_load


class DatabaseFlavourSchema(Schema):

    id = fields.String(dump_only=True)

    name = fields.String(error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    date_created = fields.Date(dump_only=True)
