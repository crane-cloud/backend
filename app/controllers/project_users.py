import json
from app.models.project_users import ProjectUser
from flask_restful import Resource, request
from app.schemas import ProjectUserSchema, UserSchema
from app.models.user import User
from app.models.role import User
from app.models.project import Project
from flask_jwt_extended import jwt_required, get_jwt_identity


class ProjectUsersView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """
        project_user_schema = ProjectUserSchema()

        project_user_data = request.get_json()

        validated_project_user_data, errors = project_user_schema.load(
            project_user_data)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get Project
        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message='Project not found'), 404

        # Get user
        user = User.find_first(email=validated_project_user_data.get('email', None))

        if not user:
            return dict(status='fail', message='User not found'), 404

        existing_user = ProjectUser.find_first(user_id=user.id, project_id=project.id)
        if existing_user:
            return dict(status='fail', message='User already exists'), 409

        # adding user to project users
        role = validated_project_user_data.get('role', None)
        new_role = ProjectUser(role=role, user_id=user.id)
        project.users.append(new_role)

        saved_project_user = project.save()

        if not saved_project_user:
            return dict(status='fail', message='Internal Server Error'), 500

        user_schema = ProjectUserSchema()
        new_project_user_data, errors = user_schema.dumps(user)

        return dict(
            status='success',
            message='User added to project successfully',
            data=dict(project_user=json.loads(new_project_user_data))
        ), 201

    @jwt_required
    def get(self, project_id):
        """
        """
        project_user_schema = ProjectUserSchema(many=True)

        project = Project.get_by_id(project_id)
        
        if not project:
            return dict(status='fail', message='Project not found'), 404

        current_user = User.get_by_id(get_jwt_identity())

        # Add current user owner of project if not listed
        existing_user = ProjectUser.find_first(user_id=current_user.id, project_id=project.id)

        if project.owner.id == current_user.id and not existing_user:
            new_role = ProjectUser(
                role="owner",
                 user_id=current_user.id
            )
            project.users.append(new_role)
            saved = project.save()
            if not saved:
                return dict(status="fail", message="Internal Server Error"), 500

        project_users = project.users

        project_user_data, errors = project_user_schema.dumps(project_users)
        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(
            status="success",
            data=dict(project_users=json.loads(project_user_data))
        ), 200


    # delete user role
    @jwt_required
    def delete(self, project_id):
        """
        """
        project_user_schema = ProjectUserSchema(partial=('role',))

        project_user_data = request.get_json()

        validated_project_user_data, errors = project_user_schema.load(
            project_user_data)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get Project
        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message='Project not found'), 404

        # Get user
        user = User.find_first(email=validated_project_user_data.get('email', None))

        if not user:
            return dict(status='fail', message='User not found'), 404

        existing_user = ProjectUser.find_first(user_id=user.id, project_id=project.id)

        if not existing_user:
            return dict(status='fail', message='User not a member of project'), 404
        
        deleted_user = ProjectUser.delete(existing_user)

        if not deleted_user:
            return dict(status='fail', message='Internal Server Error'), 500


        return dict(
            status='success',
            message='User removed from project successfully',
        ), 201
