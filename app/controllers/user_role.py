import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import UserRoleSchema
from app.models.user_role import UserRole


class UserRoleView(Resource):

    def post(self):
        """
        """

        user_role_schema = UserRoleSchema()

        user_role_data = request.get_json()

        validated_user_role_data, errors = user_role_schema.load(user_role_data)

        if errors:
            return dict(status='fail', message=errors), 400

        user_role = UserRole(**validated_user_role_data)

        saved_user_role = user_role.save()

        if not saved_user_role:
            return dict(status='fail', message='Internal Server Error'), 500

        new_user_role_data, errors = user_role_schema.dumps(user_role)

        return dict(status='success', data=dict(user_role=json.loads(new_user_role_data))), 201

    @jwt_required
    def get(self):
        """
        """

        user_role_schema = UserRoleSchema(many=True)

        user_roles = Organisation.find_all()

        user_role_data, errors = user_role_schema.dumps(user_roles)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(user_roles=json.loads(orgs_data))), 200

