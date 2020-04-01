from marshmallow import Schema, fields, validate


class ProjectSchema(Schema):

    id = fields.UUID(dump_only=True)
    name = fields.String(required=True, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
        ])
    alias = fields.String(required=True, error_message={
        "required": "alias is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='alias should be a valid string'
            ),
        ])
    owner_id = fields.UUID(required=True, error_message={
        "required": "owner_id is required"
    })
    cluster_id = fields.UUID(required=True, error_message={
        "required": "cluster_id is required"
    })
    description = fields.String()
