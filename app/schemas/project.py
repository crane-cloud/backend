from marshmallow import Schema, fields, validate
from app.helpers.age_utility import get_item_age
from app.models.app import App


class ProjectSchema(Schema):

    id = fields.UUID(dump_only=True)
    name = fields.String(required=True, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    owner_id = fields.UUID(required=True, error_message={
        "required": "owner_id is required"
    })
    cluster_id = fields.UUID(required=True, error_message={
        "required": "cluster_id is required"
    })
    description = fields.String()
    organisation = fields.String()
    project_type = fields.String()
    alias = fields.String(required=False)
    date_created = fields.Date(dump_only=True)
    age = fields.Method("get_age", dump_only=True)
    apps_count = fields.Method("get_apps_count", dump_only=True)
    disabled = fields.Boolean(dump_only=True)
    admin_disabled = fields.Boolean(dump_only=True)

    def get_age(self, obj):
        return get_item_age(obj.date_created)

    def get_apps_count(self, obj):
        return App.count(project_id=obj.id)
