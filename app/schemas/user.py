from marshmallow import Schema, fields, validate, pre_load


class UserSchema(Schema):

    id = fields.Integer(dump_only=True)

    email = fields.Email(required=True)
    name = fields.String(required=True, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
        ])
    password = fields.String(load_only=True, required=True, error_message={
        "required": "password is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='password should be a valid string'
            ),
        ])
