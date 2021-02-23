from marshmallow import Schema, fields, validate, pre_load


class ProjectDatabaseSchema(Schema):

    id = fields.String(dump_only=True)

    name = fields.String(required=True, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    user = fields.String(required=True, error_message={
        "required": "user is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='user should be a valid string'
            ),
    ])
    host = fields.String(required=True, error_message={
        "required": "host is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='host should be a valid string'
            ),
    ])
    password = fields.String(load_only=True, required=True, error_message={
        "required": "password is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='password should be a valid string'
            ),
    ])
    project_id = fields.String()
    date_created = fields.Date(dump_only=True)
