from marshmallow import Schema, fields, validate


class DeploymentSchema(Schema):

    name = fields.String(required=True, error_message={
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
    port = fields.String(required=True, error_message={
        "required": "port is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='port should be a valid string'
            ),
        ])
    replicas = fields.Integer(required=True, error_message={
        "required": "port is required"})
    kind = fields.String(required=True, error_message={
        "required": "kind is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='port should be a valid string'
            ),
        ])
    namespace = fields.String(required=True, error_message={
        "required": "namespace is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='namespace should be a valid string'
            ),
        ])
    yaml_file = fields.String(required=True, error_message={
        "required": "yaml_file is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='namespace should be a valid string'
            ),
        ])
