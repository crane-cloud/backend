import uuid
from marshmallow import Schema, fields, validate
from marshmallow import validates, ValidationError

from .role import RoleSchema
from app.helpers.age_utility import get_item_age
from .credits import CreditSchema


class UserSchema(Schema):
    id = fields.UUID(dump_only=True)

    email = fields.Email(required=True)
    name = fields.String(required=True, error_messages={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    password = fields.String(load_only=True, required=True, error_messages={
        "required": "password is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='password should be a valid string'
            ),
    ])
    roles = fields.Nested(RoleSchema, many=True, dump_only=True)
    verified = fields.Boolean(dump_only=True)
    date_created = fields.DateTime(dump_only=True)
    last_seen = fields.DateTime(dump_only=True)
    age = fields.Method("get_age", dump_only=True)
    is_beta_user = fields.Boolean()
    credits = fields.Nested(CreditSchema, many=True, dump_only=True)
    organisation = fields.String(required=True, error_messages={
        "required": "Organisation name is required"},
         validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='Organisations should be a valid string'
            ),
    ])
    disabled = fields.Boolean(dump_only=True)
    admin_disabled = fields.Boolean(dump_only=True)
   
    def get_age(self, obj):
        return get_item_age(obj.date_created)
    
    @validates('id')
    def validate_id(self, value):
        try:
            uuid.UUID(str(value))
        except ValueError:
            raise ValidationError('Not a valid UUID.')

class ActivityLogSchema(Schema):
    id = fields.UUID(dump_only=True)
    user_id = fields.UUID()
    operation = fields.String()
    status = fields.String()
    description = fields.String()
    model = fields.String()
    a_project_id = fields.String()
    a_cluster_id = fields.String()
    a_db_id = fields.String()
    a_user_id = fields.String()
    a_app_id = fields.String()
    creation_date = fields.DateTime()
    start = fields.DateTime(load_only=True)
    end = fields.DateTime(load_only=True)
