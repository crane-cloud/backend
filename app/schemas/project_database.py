from marshmallow import Schema, fields, validate, pre_load
from app.helpers.age_utility import get_item_age

class ProjectDatabaseSchema(Schema):

    id = fields.String(dump_only=True)

    name = fields.String(error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    user = fields.String(error_message={
        "required": "user is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='user should be a valid string'
            ),
    ])
    host = fields.String(error_message={
        "required": "host is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='host should be a valid string'
            ),
    ])
    password = fields.String(error_message={
        "required": "password is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='password should be a valid string'
            ),
    ])
    project_id = fields.String()
    database_flavour_name = fields.String(
        required=True,
        validate=[
            validate.OneOf(["postgres", "mysql"],
                           error='database flavour should be mysql or postgres'
                           ),
        ])

    date_created = fields.Date(dump_only=True)
    port = fields.Int()
    age = fields.Method("get_age", dump_only=True)

    def get_age(self, obj):
        return get_item_age(obj.date_created)
