import json
import os
from flask import current_app
from flask_restful import Resource, request
from flask_bcrypt import Bcrypt
from app.schemas import UserSchema
from app.models.user import User
from app.models.role import Role
from app.helpers.confirmation import send_verification
from app.helpers.token import validate_token


class UsersView(Resource):

    def post(self):
        """
        """

        user_schema = UserSchema()

        user_data = request.get_json()

        validated_user_data, errors = user_schema.load(user_data)

        email = validated_user_data.get('email', None)
        client_base_url = os.getenv(
            'CLIENT_BASE_URL',
            f'http://{request.host}/users'
            )

        # To do change to a frontend url
        verification_url = f"{client_base_url}/verify/"
        secret_key = current_app.config["SECRET_KEY"]
        password_salt = current_app.config["VERIFICATION_SALT"]
        sender = current_app.config["MAIL_DEFAULT_SENDER"]
        template = "user/verify.html"
        subject = "Please confirm your email"

        if errors:
            return dict(status="fail", message=errors), 400

        # get the customer role
        user_role = Role.find_first(name='customer')

        user_existant = User.query.filter_by(email=email).first()

        if user_existant:
            return dict(
                status="fail",
                message=f"Email {validated_user_data['email']} already in use."
                ), 400

        user = User(**validated_user_data)

        if user_role:
            user.roles.append(user_role)

        saved_user = user.save()

        if not saved_user:
            return dict(status='fail', message=f'Internal Server Error'), 500

        # send verification
        send_verification(
            email,
            user.name,
            verification_url,
            secret_key,
            password_salt,
            sender,
            current_app._get_current_object(),
            template,
            subject
            )

        new_user_data, errors = user_schema.dumps(user)

        return dict(
            status='success',
            data=dict(user=json.loads(new_user_data))
            ), 201

    def get(self):
        """
        """

        user_schema = UserSchema(many=True)

        users = User.find_all()

        users_data, errors = user_schema.dumps(users)

        if errors:
            return dict(status='fail', message=errors), 400

        return dict(
            status='success',
            data=dict(users=json.loads(users_data))
        ), 200


class UserLoginView(Resource):

    def post(self):
        """
        """

        user_schema = UserSchema(only=("email", "password"))

        token_schema = UserSchema()

        login_data = request.get_json()

        validated_user_data, errors = user_schema.load(login_data)

        if errors:
            return dict(status='fail', message=errors), 400

        email = validated_user_data.get('email', None)
        password = validated_user_data.get('password', None)

        user = User.find_first(email=email)

        if not user:
            return dict(status='fail', message="login failed"), 401

        if not user.verified:
            return dict(
                status='fail',
                message='email not verified', data=dict(verified=user.verified)
                ), 401

        user_dict, errors = token_schema.dump(user)

        if user and user.password_is_valid(password):

            access_token = user.generate_token(user_dict)

            if not access_token:
                return dict(
                    status="fail",
                    message="Internal Server Error"
                    ), 500

            return dict(
                status='success',
                data=dict(
                    access_token=access_token,
                    email=user.email,
                    username=user.username,
                    verified=user.verified,
                    id=str(user.id),
                    )), 200

        return dict(status='fail', message="login failed"), 401


class UserDetailView(Resource):

    def get(self, user_id):
        """
        """
        user_schema = UserSchema()

        user = User.get_by_id(user_id)

        if not user:
            return dict(
                status='fail',
                message=f'user {user_id} not found'
                ), 404

        user_data, errors = user_schema.dumps(user)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            user=json.loads(user_data))), 200

    def delete(self, user_id):
        """
        """

        try:
            user = User.get_by_id(user_id)

            if not user:
                return dict(
                    status='fail',
                    message=f'user {user_id} not found'
                    ), 404

            deleted = user.delete()

            if not deleted:
                return dict(status='fail', message='deletion failed'), 500

            return dict(
                status='success',
                message=f'user {user_id} deleted successfully'
                ), 200

        except Exception as e:
            return dict(status='fail', message=str(e)), 500

    def patch(self, user_id):
        """
        """
        try:
            user_schema = UserSchema(only=("name",))

            user_data = request.get_json()

            validate_user_data, errors = user_schema.load(user_data)

            if errors:
                return dict(status='fail', message=errors), 400

            user = User.get_by_id(user_id)

            if not user:
                return dict(
                    status='fail',
                    message=f'User {user_id} not found'
                    ), 404

            updated = User.update(user, **validate_user_data)

            if not updated:
                return dict(
                    status='fail',
                    message='Internal Server Error'
                    ), 500

            return dict(
                status='success',
                message=f'User {user_id} updated successfully'
                ), 200

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class AdminLoginView(Resource):

    def post(self):
        """
        """

        user_schema = UserSchema(only=("email", "password"))

        token_schema = UserSchema()

        login_data = request.get_json()

        validated_user_data, errors = user_schema.load(login_data)

        if errors:
            return dict(status='fail', message=errors), 400

        email = validated_user_data.get('email', None)
        password = validated_user_data.get('password', None)

        user = User.find_first(email=email)
        admin_role = Role.find_first(name='administrator')

        if not user or not admin_role or (admin_role not in user.roles):
            return dict(status='fail', message="login failed"), 401

        if not user.verified:
            return dict(
                status='fail',
                message='Email not verified',
                data=dict(verified=user.verified)
                ), 401

        user_dict, errors = token_schema.dump(user)

        if user and user.password_is_valid(password):

            access_token = user.generate_token(user_dict)

            if not access_token:
                return dict(
                    status="fail", message="Internal Server Error"), 500

            return dict(
                status='success',
                data=dict(
                    access_token=access_token,
                    email=user.email,
                    username=user.username,
                    verified=user.verified,
                    id=str(user.id),
                    )), 200

        return dict(status='fail', message="login failed"), 401


class UserEmailVerificationView(Resource):

    def get(self, token):
        """
        """

        user_schema = UserSchema()

        secret = current_app.config["SECRET_KEY"]
        salt = current_app.config["VERIFICATION_SALT"]

        email = validate_token(token, secret, salt)

        if not email:
            return dict(status="fail", message="invalid token"), 401

        user = User.find_first(**{'email': email})

        if not user:
            return dict(
                status='fail',
                message=f'User with email {email} not found'
                ), 404

        if user.verified:
            return dict(
                status='fail', message='Email is already verified'), 400

        user.verified = True

        user_saved = user.save()

        user_dict, _ = user_schema.dump(user)

        if user_saved:

            # generate access token
            access_token = user.generate_token(user_dict)

            if not access_token:
                return dict(
                    status='fail', message='Internal Server Error'), 500

            return dict(
                status='success',
                message='Email verified successfully',
                data=dict(
                    access_token=access_token,
                    email=user.email,
                    username=user.username,
                    verified=user.verified,
                    id=str(user.id),
                    )), 200

        return dict(status='fail', message='Internal Server Error'), 500


class EmailVerificationRequest(Resource):

    def post(self):
        """
        """
        email_schema = UserSchema(only=("email",))

        request_data = request.get_json()

        validated_data, errors = email_schema.load(request_data)

        if errors:
            return dict(status='fail', message=errors), 400

        email = validated_data.get('email', None)
        client_base_url = os.getenv(
            'CLIENT_BASE_URL',
            f'http://{request.host}/users'
            )

        # To do, change to a frontend url
        verification_url = f"{client_base_url}/verify/"
        secret_key = current_app.config["SECRET_KEY"]
        password_salt = current_app.config["VERIFICATION_SALT"]
        sender = current_app.config["MAIL_DEFAULT_SENDER"]
        template = "user/verify.html"
        subject = "Please confirm your email"

        user = User.find_first(**{'email': email})

        if not user:
            return dict(
                status='fail',
                message=f'User with email {email} not found'
                ), 404

        # send verification
        send_verification(
            email,
            user.name,
            verification_url,
            secret_key,
            password_salt,
            sender,
            current_app._get_current_object(),
            template,
            subject
            )

        return dict(
            status='success',
            message=f'Verification link sent to {email}'
            ), 200


class ForgotPasswordView(Resource):

    def post(self):
        """
        """

        email_schema = UserSchema(only=("email",))

        request_data = request.get_json()
        validated_data, errors = email_schema.load(request_data)

        if errors:
            return dict(status='fail', message=errors), 400

        email = validated_data.get('email', None)
        client_base_url = os.getenv(
            'CLIENT_BASE_URL',
            f'http://{request.host}/users'
            )

        verification_url = f"{client_base_url}/reset_password/"
        secret_key = current_app.config["SECRET_KEY"]
        password_salt = current_app.config["PASSWORD_SALT"]
        sender = current_app.config["MAIL_DEFAULT_SENDER"]
        template = "user/reset.html"
        subject = "Password reset"

        user = User.find_first(**{'email': email})

        if not user:
            return dict(
                status='fail',
                message=f'User with email {email} not found'
                ), 404

        # send password reset link
        send_verification(
            email,
            user.name,
            verification_url,
            secret_key,
            password_salt,
            sender,
            current_app._get_current_object(),
            template,
            subject
        )

        return dict(
            status='success',
            message=f'Password reset link sent to {email}'
            ), 200


class ResetPasswordView(Resource):

    def post(self, token):

        password_schema = UserSchema(only=("password",))

        secret = current_app.config["SECRET_KEY"]
        salt = current_app.config["PASSWORD_SALT"]

        request_data = request.get_json()
        validated_data, errors = password_schema.load(request_data)

        if errors:
            return dict(status='fail', message=errors), 400

        password = validated_data['password']

        hashed_password = Bcrypt().generate_password_hash(password).decode()

        email = validate_token(token, secret, salt)

        if not email:
            return dict(status='fail', message="invalid token"), 401

        user = User.find_first(**{'email': email})

        if not user:
            return dict(
                status="fail",
                message=f'user with email {email} not found'
                ), 404

        if not user.verified:
            return dict(
                status='fail', message=f'email {email} is not verified'), 400

        user.password = hashed_password

        user_saved = user.save()

        if not user_saved:
            return dict(status='fail', message='internal server error'), 500

        return dict(
            status='success', message='password reset successfully'), 200
