import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import UserRoleSchema, UserSchema
from app.models.user_role import UserRole
from app.schemas.role import RoleSchema
from app.models.user import User
from app.models.role import Role
from app.helpers.decorators import admin_required


class UserRolesView(Resource):

    @admin_required
    def post(self, user_id):
        """
        """

        user_role_schema = UserRoleSchema()

        user_role_data = request.get_json()

        validated_user_role_data, errors = user_role_schema.load(
            user_role_data)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get User
        user = User.get_by_id(user_id)

        if not user:
            return dict(status='fail', message='User not found'), 404

        # Get role
        role = Role.get_by_id(validated_user_role_data.get('role_id', None))

        if not role:
            return dict(status='fail', message='Role not found'), 404

        if role in user.roles:
            return dict(status='fail', message='User already has role'), 409

        # adding role to user roles
        if role in user.roles:
            return dict(status='fail', message='Role already Exists'), 404

        user.roles.append(role)

        saved_user_role = user.save()

        user_schema = UserSchema()

        if not saved_user_role:
            return dict(status='fail', message='Internal Server Error'), 500

        new_user_role_data, errors = user_schema.dumps(user)

        return dict(
            status='success',
            data=dict(user_role=json.loads(new_user_role_data))
        ), 201

    @admin_required
    def get(self, user_id):
        """
        """
        role_schema = RoleSchema(many=True)

        user = User.get_by_id(user_id)

        if not user:
            return dict(status='fail', message='User not found'), 404

        user_roles = user.roles

        user_role_data, errors = role_schema.dumps(user_roles)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(
            status="success",
            data=dict(user_roles=json.loads(user_role_data))
        ), 200

    # delete user role

    @admin_required
    def delete(self, user_id):
        """
        """
        user_role_schema = UserRoleSchema()

        user_role_data = request.get_json()

        validated_user_role_data, errors = user_role_schema.load(
            user_role_data)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get User
        user = User.get_by_id(user_id)

        if not user:
            return dict(status='fail', message='User not found'), 404

        # Get role
        role = Role.get_by_id(validated_user_role_data.get('role_id', None))

        if not role:
            return dict(status='fail', message='Role not found'), 404

        # removing user from role
        try:
            user.roles.remove(role)
        except Exception:
            return dict(status='fail', message='User role not found'), 404

        saved_user_role = user.save()

        user_schema = UserSchema()

        if not saved_user_role:
            return dict(status='fail', message='Internal Server Error'), 500

        new_user_role_data, errors = user_schema.dumps(user)

        return dict(
            status='success',
            data=dict(user_role=json.loads(new_user_role_data))
        ), 201
