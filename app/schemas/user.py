from app.helpers.role_search import has_admin_role
from app.models.project import Project
from app.models.app import App
from app.models import db
from app.schemas.common import BaseSchema
from sqlalchemy import func
from app.models.project_users import ProjectFollowers, ProjectUser
from app.models.tags import TagFollowers
from app.models.user import Followers
from marshmallow import Schema, fields, validate, pre_load, ValidationError, validates_schema
from app.helpers.user_finder import validate_login_identifier
import re

from .role import RoleSchema
from app.helpers.age_utility import get_item_age
from .credits import CreditSchema


class EmailOrUsernameField(fields.String):
    """Custom field that accepts either email or username"""

    def _validate(self, value):
        """Validate the email or username"""
        if not value:
            raise ValidationError('Username or email is required')

        validation_result = validate_login_identifier(value)
        if not validation_result['valid']:
            raise ValidationError(validation_result['message'])

        return value


class SocialLinksField(fields.Dict):
    """Custom field for social links with predefined acceptable keys"""

    ALLOWED_PLATFORMS = {
        'twitter', 'facebook', 'instagram', 'linkedin', 'github',
        'gitlab', 'bitbucket', 'stackoverflow', 'youtube', 'tiktok',
        'discord', 'telegram', 'whatsapp', 'website', 'blog', 'portfolio'
    }

    def _validate(self, value):
        """Validate that only allowed keys are used"""
        if not isinstance(value, dict):
            raise ValidationError('Social links must be a dictionary')

        # Check for invalid keys
        invalid_keys = set(value.keys()) - self.ALLOWED_PLATFORMS
        if invalid_keys:
            raise ValidationError(
                f"Invalid social platform(s): {', '.join(invalid_keys)}. "
                f"Allowed platforms: {', '.join(sorted(self.ALLOWED_PLATFORMS))}"
            )

        # Validate URLs
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$|^@[a-zA-Z0-9_]+$'
        for platform, url in value.items():
            if not isinstance(url, str) or not url.strip():
                raise ValidationError(
                    f"URL for {platform} must be a non-empty string")

            # Basic URL validation (you can make this more sophisticated)
            if not re.match(url_pattern, url.strip()):
                raise ValidationError(
                    f"Invalid URL format for {platform}: {url}")

        return value


class UserSchema(BaseSchema):
    id = fields.String(dump_only=True)

    email = fields.Email(required=True)
    name = fields.String(required=True, error_message={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    username = fields.String(required=False, error_message={
        "required": "username is required"},
        validate=[
            validate.Regexp(
                regex=r'^[a-zA-Z0-9_-]+$', error='username should contain only letters, numbers, underscores, and hyphens'
            ),
            validate.Length(
                min=3, max=30, error='username must be between 3 and 30 characters')
    ]
    )
    password = fields.String(load_only=True, required=True, error_message={
        "required": "password is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='password should be a valid string'
            ),
    ])
    roles = fields.Nested(RoleSchema, many=True, dump_only=True)
    verified = fields.Boolean(dump_only=True)
    last_seen = fields.Date(dump_only=True)
    age = fields.Method("get_age", dump_only=True)
    is_beta_user = fields.Boolean()
    credits = fields.Nested(CreditSchema, many=True, dump_only=True)
    organisation = fields.String(required=True, error_message={
        "required": "Organisation name is required"},
        validate=[
        validate.Regexp(
            regex=r'^(?!\s*$)', error='Organisations should be a valid string'
        ),
    ])
    is_public = fields.Boolean()
    profile_picture = fields.String()
    biography = fields.String()
    social_links = SocialLinksField(
        missing={},
        allow_none=True,
        error_message="Invalid social links format"
    )
    followers_count = fields.Method("get_followers_count", dump_only=True)
    following_count = fields.Method("get_following_count", dump_only=True)
    owned_projects_count = fields.Method(
        "get_owned_projects_count", dump_only=True)
    owned_apps_count = fields.Method(
        "get_owned_apps_count", dump_only=True)
    followed_tags_count = fields.Method(
        "get_followed_tags_count", dump_only=True)
    collaborative_projects_count = fields.Method(
        "get_collaborative_projects_count", dump_only=True)
    followed_projects_count = fields.Method(
        "get_followed_projects_count", dump_only=True)

    def get_age(self, obj):
        return get_item_age(obj.date_created)

    def get_followers_count(self, obj):
        return Followers.count(followed_id=obj.id)

    def get_following_count(self, obj):
        return Followers.count(follower_id=obj.id)

    def get_owned_projects_count(self, obj):
        return Project.count(
            owner_id=obj.id,
            deleted=False,
            disabled=False,
            admin_disabled=False,
            is_public=True
        )

    def get_owned_apps_count(self, obj):
        return db.session.query(func.count(App.id)).join(
            Project, App.project_id == Project.id
        ).filter(
            Project.owner_id == obj.id,
            Project.deleted.is_(False),
            Project.disabled.is_(False),
            Project.admin_disabled.is_(False),
            Project.is_public.is_(True),
            App.deleted.is_(False),
            App.disabled.is_(False),
            App.admin_disabled.is_(False),
        ).scalar()

    def get_followed_tags_count(self, obj):
        return TagFollowers.count(user_id=obj.id)

    def get_collaborative_projects_count(self, obj):
        return ProjectUser.count(user_id=obj.id)

    def get_followed_projects_count(self, obj):
        return ProjectFollowers.count(user_id=obj.id)


class LoginSchema(Schema):
    """Schema for login with email or username - supports both 'email' and 'username' fields"""
    username = EmailOrUsernameField(required=False, error_message={
        "required": "Username or email is required"
    })
    email = fields.String(required=False)  # For backward compatibility
    password = fields.String(required=True, error_message={
        "required": "Password is required"
    })

    @pre_load
    def process_email_to_username(self, data, **kwargs):
        """If email is passed, use its value to fill username field"""
        if isinstance(data, dict):
            # If email is provided but username is not, use email value for username
            if 'email' in data and 'username' not in data:
                data['username'] = data['email']
            # If both email and username are provided, username takes precedence
            elif 'email' in data and 'username' in data:
                # Username takes precedence, remove email from data
                pass
            # Remove email from final data as we only use username internally
            if 'email' in data:
                data.pop('email', None)
        return data

    @validates_schema
    def validate_username_or_email(self, data, **kwargs):
        """Custom validation to ensure either username or email is provided"""
        errors = {}
        if not data.get('username'):
            errors['username'] = ['Username or email is required']

        if errors:
            raise ValidationError(errors)


class SimpleUserSchema(Schema):
    id = fields.String(dump_only=True)
    email = fields.Email(dump_only=True)
    username = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    verified = fields.Boolean(dump_only=True)
    profile_picture = fields.String(dump_only=True)
    is_admin = fields.Method("get_is_admin", dump_only=True)
    followers_count = fields.Method("get_followers_count", dump_only=True)
    following_count = fields.Method("get_following_count", dump_only=True)

    def get_is_admin(self, obj):
        if has_admin_role(obj.roles):
            return True
        return False

    def get_followers_count(self, obj):
        return Followers.count(followed_id=obj.id)

    def get_following_count(self, obj):
        return Followers.count(follower_id=obj.id)


class UserListSchema(Schema):
    id = fields.String(dump_only=True)
    email = fields.Email(required=True)
    name = fields.String(required=True)
    organisation = fields.String(required=True)
    last_seen = fields.Date(dump_only=True)
    profile_picture = fields.String()


class ActivityLogSchema(Schema):
    id = fields.String(dump_only=True)
    user_id = fields.String()
    operation = fields.String()
    status = fields.String()
    description = fields.String()
    model = fields.String()
    a_project_id = fields.String()
    a_cluster_id = fields.String()
    a_db_id = fields.String()
    a_user_id = fields.String()
    a_app_id = fields.String()
    creation_date = fields.Date()
    start = fields.Date(load_only=True)
    end = fields.Date(load_only=True)
