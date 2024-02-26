from functools import partial
import json
from app.models.project_users import ProjectUser
from flask_restful import Resource, request
from app.schemas import ProjectUserSchema, UserSchema, AnonymousUsersSchema
from app.models.user import User
from app.models.role import User
from app.models.project import Project
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.admin import is_authorised_project_user, is_owner_or_admin
from flask import current_app
from app.helpers.user_to_project_notification import send_user_to_project_notification
from app.helpers.user_role_update_notification import send_user_role_update_notification
from datetime import date
from app.models.anonymous_users import AnonymousUser

class ProjectUsersView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_user_schema = ProjectUserSchema()

        invitation_data = request.get_json()
        resend_invite = invitation_data.pop('resend', False)
        

        project_user_data = invitation_data

        validated_project_user_data, errors = project_user_schema.load(
            project_user_data)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get Project
        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message='Project not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id ,'admin'):
                return dict(status='fail', message='unauthorised'), 403

        # Get user
        user = User.find_first(email=validated_project_user_data.get('email', None))

        if not user:
            # register anonymous user
            anonymous_user_email = validated_project_user_data.get('email', None)
            anonymous_user_exists = AnonymousUser.find_first(email=anonymous_user_email, project_id=project.id)

            if anonymous_user_exists:
                return dict(status='fail', message='Annoymous user already exists'), 500

            
            role = validated_project_user_data.get('role', None)
            if role == 'owner':
                return dict(status='fail', message='User cannot be added as owner'), 400
            
            if not resend_invite :
                new_anonymous_user = AnonymousUser(email=anonymous_user_email, project_id=project.id, role=role)
                saved_anonymous_user = new_anonymous_user.save()

                if not saved_anonymous_user:
                    return dict(status='fail', message='Internal Server Error'), 500
            
            # send anonymous user an invite email.
            inviting_user = User.get_by_id(current_user_id)
            name = inviting_user.name
            template = "user/anonymous_user_to_project.html"
            subject = "Invitation to collaborate on Project in Cranecloud"
            email =anonymous_user_email
            today = date.today()
            project_name = project.name
            email_role = role

            # send email
            # success = True # failed to see it's relevance
            send_user_to_project_notification(
            email,
            name,
            current_app._get_current_object(),
            template,
            subject,
            today.strftime("%m/%d/%Y"),
            project_name,
            email_role, 
            success)           


            return dict(status='success', message='Anymous user successfully added to project'), 201
        

        existing_user = ProjectUser.find_first(user_id=user.id, project_id=project.id)


        if (existing_user and not resend_invite):
            return dict(status='fail', message='User already exists'), 409
        
        if (existing_user):
            if (existing_user.accepted_collaboration_invite) :
                return dict(status = 'fail' , message = 'User already accepted the invitation') , 409
        
        # adding user to project users
        role = validated_project_user_data.get('role', None)
        if role == 'owner':
            return dict(status='fail', message='User cannot be added as owner'), 400
        
        if not resend_invite :
            new_role = ProjectUser(role=role, user_id=user.id, accepted_collaboration_invite=False)
            project.users.append(new_role)

            saved_project_user = project.save()

            if not saved_project_user:
                return dict(status='fail', message='Internal Server Error'), 500

         # send email variable
        name = user.name
        template = "user/user_to_project.html"
        subject = "Assignment to Project from Crane Cloud"
        email =user.email
        today = date.today()
        project_name = project.name
        email_role = role
        success = False

        # send email
        success = True
        send_user_to_project_notification(
        email,
        name,
        current_app._get_current_object(),
        template,
        subject,
        today.strftime("%m/%d/%Y"),
        project_name,
        email_role, 
        success)

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
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_user_schema = ProjectUserSchema(many=True)
        anonymous_user_schema = AnonymousUsersSchema(many=True)

        project = Project.get_by_id(project_id)
        
        if not project:
            return dict(status='fail', message='Project not found'), 404
        
        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id ,'member'):
                return dict(status='fail', message='unauthorised'), 403

        current_user = User.get_by_id(current_user_id)

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
        
        project_anonymous_users = project.anonymoususers

        project_anonymous_user_data, errors = anonymous_user_schema.dumps(project_anonymous_users)
        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(
            status="success",
            data=dict(project_users=json.loads(project_user_data),project_anonymous_users=json.loads(project_anonymous_user_data))
        ), 200

    @jwt_required
    def patch(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

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

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id ,'admin'):
                return dict(status='fail', message='unauthorised'), 403

        # Get user
        user = User.find_first(email=validated_project_user_data.get('email', None))

        if not user:
            return dict(status='fail', message='User not found'), 404
        
        # Check if user is owner
        if user.id == project.owner.id:
            return dict(status='fail', message='User is the owner of project'), 400

        existing_user = ProjectUser.find_first(user_id=user.id, project_id=project.id)
        if not existing_user:
            return dict(status='fail', message='User is not part of the project'), 404

        # updating user role
        role = validated_project_user_data.get('role', None)

        if role == 'owner':
            return dict(status='fail', message='User role cannot be updated to owner'), 400

        if f'RolesList.{role}' == str(existing_user.role):
            return dict(status='fail', message='User is already {}'.format(role)), 400

        updated = ProjectUser.update(existing_user, role=role)

        if not updated:
            return dict(status='fail', message='Internal Server Error'), 500

         # send email variable
        name = user.name
        template = "user/user_role_update.html"
        subject = "Update User Role from Crane Cloud"
        email =user.email
        today = date.today()
        project_name = project.name
        success = False
        email_role = role

        # send email
        success = True
        send_user_role_update_notification(
        email,
        name,
        current_app._get_current_object(),
        template,
        subject,
        today.strftime("%m/%d/%Y"),
        project_name,
        email_role, 
        success)


        user_schema = ProjectUserSchema()
        updated_project_user_data, errors = user_schema.dumps(existing_user)

        return dict(
            status='success',
            message='User role updated successfully',
            data=dict(project_user=json.loads(updated_project_user_data))
        ), 200


    # delete user from project
    @jwt_required
    def delete(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

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

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id ,'admin'):
                return dict(status='fail', message='unauthorised'), 403

        # Get user
        user = User.find_first(email=validated_project_user_data.get('email', None))

        if not user:
            # check if this user exists as an anonymous user
            anonymous_user_email = validated_project_user_data.get('email', None)
            anonymous_user_exists = AnonymousUser.find_first(email=anonymous_user_email, project_id=project.id)

            if not anonymous_user_exists:
                return dict(status='fail', message='User not found'), 404

            deleted_anonymous_user = AnonymousUser.delete(anonymous_user_exists)
            
            if not deleted_anonymous_user:
                return dict(status='fail', message='Internal Server Error'), 500

            return dict(
            status='success',
            message='Anonymous user removed from project successfully',
        ), 201

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



class ProjectUsersTransferView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

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

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        # Get user
        user = User.find_first(email=validated_project_user_data.get('email', None))

        if not user:
            return dict(status='fail', message='User not found'), 404

        if user.id == project.owner.id:
            return dict(status='fail', message='User is the owner of project'), 400

        existing_user = ProjectUser.find_first(user_id=user.id, project_id=project.id)

        owner_user = ProjectUser.find_first(role='owner', project_id=project.id)

        if owner_user:
            # updating user role
            updated = ProjectUser.update(owner_user, role='admin')
            if not updated:
                return dict(status='fail', message='Internal Server Error'), 500

        #  Make user project owner
        if existing_user:
            updated_user = ProjectUser.update(existing_user, role='owner')
            if not updated_user:
                return dict(status='fail', message='Internal Server Error'), 500

        else:
            new_role = ProjectUser(role='owner', user_id=user.id)
            project.users.append(new_role)

        # Make the use project owner 
        project.owner_id = user.id
        saved_project_user = project.save()

        if not saved_project_user:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(
            status='success',
            message='Project has been transfered successfully',
        ), 201

class ProjectUsersHandleInviteView(Resource):

    @jwt_required
    def patch(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()

        project_user_schema = ProjectUserSchema(partial=True, exclude=["email","role"])

        project_user_data = request.get_json()

        validated_project_user_data, errors = project_user_schema.load(
            project_user_data, partial=True)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get Project
        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message='Project not found'), 404

        # Get user
        user = User.get_by_id(current_user_id)

        if not user:
            return dict(status='fail', message='User not found'), 404

        if user.id == project.owner.id:
            return dict(status='fail', message='User is the owner of project and cannot be invited'), 400

        existing_user = ProjectUser.find_first(user_id=user.id, project_id=project.id)

        if not existing_user:
            return dict(status='fail', message='User is not part of project'), 404

        # updating user project collaboration invite 
        invite_status = validated_project_user_data.get('accepted_collaboration_invite', None)

        if invite_status == False:
            deleted_user = ProjectUser.delete(existing_user)

            if not deleted_user:
                return dict(status='fail', message='Internal Server Error'), 500
            
            return dict(status='success', message='User successfully removed from the project'), 201
        
        updated = ProjectUser.update(existing_user, accepted_collaboration_invite=invite_status)

        if not updated:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(
            status='success',
            message='Invite to project has successfully been accepted',
        ), 201