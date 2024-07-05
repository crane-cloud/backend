import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import RoleSchema
from marshmallow import ValidationError
from app.models.role import Role
from app.helpers.decorators import admin_required


class RolesView(Resource):
    @admin_required
    def post(self):
        """
        """

        roles_schema = RoleSchema()

        roles_data = request.get_json()

        try:
            validated_role_data = roles_schema.load(roles_data)
            role_name = validated_role_data.get('name', None)
        except ValidationError as err:
            return dict(status='fail', message=err.messages), 400

        role_existant = Role.find_first(name=role_name)

        if role_existant:
            return dict(
                status="fail",
                message=f"Role {validated_role_data['name']} Already Exists."
            ), 400

        role = Role(**validated_role_data)
        saved_role = role.save()

        if not saved_role:
            return dict(status='fail', message=f'Internal Server Error'), 500

        try:
            new_role_data = roles_schema.dumps(role)
        except ValidationError as err:
            return dict(status='fail', message=err.messages), 400

        return dict(
            status='success',
            data=dict(role=json.loads(new_role_data))
        ), 201

    @admin_required
    def get(self):
        """
        """
        role_schema = RoleSchema(many=True)

        roles = Role.find_all()

        try:
            roles_data = role_schema.dumps(roles)
        except ValidationError as err:
            return dict(status='fail', message=err.messages), 400

        return dict(
            status='success',
            data=dict(roles=json.loads(roles_data))
        ), 200


class RolesDetailView(Resource):

    @admin_required
    def get(self, role_id):
        """
        """
        role_schema = RoleSchema()

        role = Role.get_by_id(role_id)

        if not role:
            return dict(
                status="fail",
                message=f"Role with id {role_id} not found"
            ), 404

        try:
            role_data = role_schema.dumps(role)
        except ValidationError as err:
            return dict(status='fail', message=err.messages), 500

        return dict(
            status='success',
            data=dict(role=json.loads(role_data))
        ), 200

    @admin_required
    def patch(self, role_id):
        """
        """

        # To do check if user is admin

        role_schema = RoleSchema(partial=True)

        update_data = request.get_json()

        try:
            validated_update_data = role_schema.load(update_data)
        except ValidationError as err:
            return dict(status='fail', message=err.messages), 400

        role = Role.get_by_id(role_id)

        if not role:
            return dict(
                status="fail",
                message=f"Role with id {role_id} not found"
            ), 404

        if 'name' in validated_update_data:
            role.name = validated_update_data['name']

        updated_role = role.save()

        if not updated_role:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(
            status="success",
            message=f"Role {role.name} updated successfully"
        ), 200

    @admin_required
    def delete(self, role_id):
        """
        """
        # To do get current user and check if the user is admin

        role = Role.get_by_id(role_id)

        if not role:
            return dict(
                status="fail",
                message=f"Role with id {role_id} not found"
            ), 404

        deleted_role = role.delete()

        if not deleted_role:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status='success', message="Successfully deleted"), 200
