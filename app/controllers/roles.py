import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import RoleSchema
from app.models.role import Role


class RolesView(Resource):
    def post(self):
        """
        """

        roles_schema = RoleSchema()

        roles_data = request.get_json()

        validated_role_data, errors = roles_schema.load(roles_data)

        role_name = validated_role_data.get('name', None)

        if errors:
            return dict(status="fail", message=errors), 400

        role_existant = Role.find_first(name=role_name)

        if role_existant:
            return dict(status="fail", message=f"Role {validated_role_data['name']} Already Exists."), 400

        role = Role(**validated_role_data)
        saved_role = role.save()

        if not saved_role:
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_role_data, errors = roles_schema.dumps(role)

        return dict(status='success', data=dict(role=json.loads(new_role_data))), 201

    def get(self):
        """
        """

        role_schema = RoleSchema(many=True)

        roles = Role.find_all()

        roles_data, errors = role_schema.dumps(roles)

        if errors:
            return dict(status='fail', message=errors), 400

        return dict(
            status='success',
            data=dict(users=json.loads(roles_data))
        ), 200

        # Todo: Delete, Update and get Single role (Patch delete Get)
        # 