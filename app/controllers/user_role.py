import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import UserRoleSchema
from app.models.user_role import UserRole
from app.schemas.role import RoleSchema
from app.models.user import User


class UserRolesView(Resource):

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

    def get(self):
        """
        """

        user_role_schema = UserRoleSchema(many=True)

        user_roles = UserRole.find_all()

        user_role_data, errors = user_role_schema.dumps(user_roles)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(user_roles=json.loads(user_role_data))), 200


class UserRolesDetailView(Resource):

    def get(self, user_id):
        role_schema = RoleSchema(many=True)
        
        roles = self.getUserRoles(user_id)

        role_data, errors = role_schema.dumps(roles)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(user_roles=json.loads(role_data))), 200

    def getUserRoles(self, user_id):
        user = User.find_first(id=user_id)
        if not user:
            # return dict(status='fail', message='Internal Server Error'), 500
            return False

        return user.roles

    """ This should return Tru if user has the role """
    def checkUserRole(self, user_id, role_name):
        roles = self.getUserRoles(user_id)

        # TODO: handle case if is user doesnt exit
        
        if roles is False:
            return False

        for role in roles:
            if (role.name == role_name):
                return True

    

