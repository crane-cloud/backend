from marshmallow import Schema, fields, validate, pre_load

from .role import RoleSchema


class UserSchema(Schema):

    id = fields.String(dump_only=True)

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
    roles = fields.Nested(RoleSchema, many=True, dump_only=True)
    verified = fields.Boolean(dump_only=True)
    date_created = fields.Date(dump_only=True)
