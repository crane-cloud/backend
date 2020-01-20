from marshmallow import Schema, fields, validate, pre_load


class RoleSchema(Schema):

    id = fields.Integer(dump_only=True)
    # uuid = fields.Integer(dump_only=True)
    name = fields.String(required=True, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
        ])
    
