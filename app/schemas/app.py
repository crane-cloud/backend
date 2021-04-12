from marshmallow import Schema, fields, validate


class AppSchema(Schema):

    id = fields.String(dump_only=True)

    name = fields.String(required=True, error_messgae={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
        ])
    image = fields.String(required=True, error_message={
        "required": "image is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='image should be a valid string'
            ),
        ])
    project_id = fields.String(required=True, error_message={
        "required": "project_id is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='project_id should be a valid string'
            ),
        ])
    alias = fields.String()
    url = fields.Url(dump_only=True)
    env_vars = fields.Dict()
    port = fields.Int()
    command = fields.String()
    private_image = fields.Bool()
    docker_server = fields.String()
    docker_username = fields.String()
    docker_password = fields.String()
    docker_email = fields.String()
    replicas = fields.Int(validate=validate.Range(min=1, max=4))
    date_created = fields.Date(dump_only=True)
