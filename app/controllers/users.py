import json
import os
from flask import current_app
from flask_restful import Resource, request
from flask_bcrypt import Bcrypt
from app.schemas import UserSchema, UserGraphSchema
from app.models.user import User
from app.models.role import Role
from app.helpers.confirmation import send_verification
from app.helpers.token import validate_token
from app.helpers.decorators import admin_required
import requests
import secrets
import string
from sqlalchemy import func, column
from app.models import db
from datetime import date, datetime


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
            f'https://{request.host}/users'
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

    @admin_required
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


class UserAdminUpdateView(Resource):

    @admin_required
    def patch(self):
        try:
            user_schema = UserSchema(only=("is_beta_user",))

            user_data = request.get_json()
            user_id = user_data["user_id"]

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

        #Updating user's last login
        user.last_seen = datetime.datetime.now()
        updated_user = user.save()

        if not updated_user:
            return dict(status='fail', message='Internal Server Error(Cannot update last login time)'), 500

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
                    is_beta_user=user.is_beta_user,
                    name= user.name,
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
            f'https://{request.host}/users'
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
            f'https://{request.host}/users'
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


class OAuthView(Resource):

    def post(self):
        """
        """
        token_schema = UserSchema(partial=("password"),)

        request_data = request.get_json()

        if not request_data:
            return dict(
                status='fail',
                message='No data received'
            ), 400

        # Github Oauth
        code = request_data.get('code')
        if not code:
            return dict(
                status='fail',
                message='No code received'
            ), 400

        data = {
            'client_id': current_app.config.get('GITHUB_CLIENT_ID'),
            'client_secret': current_app.config.get('GITHUB_CLIENT_SECRET'),
            'code': code
        }

        # exchange the 'code' for an access token
        response = requests.post(
            url='https://github.com/login/oauth/access_token',
            data=data,
            headers={'Accept': 'application/json'}
        )

        if response.status_code != 200:
            return dict(status='fail', message="User authentication failed"), 401

        response_json = response.json()

        if response_json.get('error'):
            return dict(status='fail',
                        message=f"{response_json['error'], response_json['error_description']}"), 401

        access_token = response_json['access_token']

        # get the user details using the access token
        user_response = requests.get(
            url='https://api.github.com/user',
            headers={
                'Accept': 'application/json',
                'Authorization': f'token {access_token}'
            }
        )

        if user_response.status_code != 200:
            return dict(status='fail', message="User authentication failed"), 401

        res_json = user_response.json()

        name = res_json.get('name')
        if not name:
            name = res_json['login']
        username = res_json['login']
        email = res_json['email']

        if not email:
            new_res = requests.get(
                url='https://api.github.com/user/emails',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'token {access_token}'
                }
            )
            res_json = new_res.json()
            email = res_json[0]['email']

        user = User.find_first(email=email)

        # create the user
        if not user:
            user = User(
                email=email,
                name=name,
                password=''.join((secrets.choice(string.ascii_letters)
                                  for i in range(24))),
            )
            user.verified = True
            user.username = username
            saved_user = user.save()

            if not saved_user:
                return dict(status='fail', message=f'Internal Server Error'), 500

        # update user info
        user.name = name
        user.username = username
        user.verified = True
        updated_user = user.save()

        if not updated_user:
            return dict(status='fail', message='Internal Server Error'), 500

        # create user token
        user_dict, errors = token_schema.dump(user)

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
                name=user.name,
                username=user.username,
                verified=user.verified,
                id=str(user.id),
            )), 200


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


class UserDataSummaryView(Resource):

    @admin_required
    def post(self):
        """
        Shows new users per month or year
        """
        user_filter_data = request.get_json()
        filter_schema = UserGraphSchema()

        validated_query_data, errors = filter_schema.load(user_filter_data)

        if errors:
            return dict(status='fail', message=errors), 400

        start = validated_query_data.get('start', '2018-01-01')
        end = validated_query_data.get('end', datetime.now())
        set_by = validated_query_data.get('set_by', 'month')
        total_users = len(User.find_all())
        if set_by == 'month':
            date_list = func.generate_series(
                start, end, '1 month').alias('month')
            month = column('month')

            user_data = db.session.query(month, func.count(User.id)).\
                select_from(date_list).\
                outerjoin(User, func.date_trunc('month', User.date_created) == month).\
                group_by(month).\
                order_by(month).\
                all()

        else:
            date_list = func.generate_series(
                start, end, '1 year').alias('year')
            year = column('year')

            user_data = db.session.query(year, func.count(User.id)).\
                select_from(date_list).\
                outerjoin(User, func.date_trunc('year', User.date_created) == year).\
                group_by(year).\
                order_by(year).\
                all()

        user_info = []
        for item in user_data:
            item_dict = {
                'year': item[0].year, 'month': item[0].month, 'value': item[1]
            }
            user_info.append(item_dict)
        return dict(
            status='success',
            data=dict(
                metadata=dict(total_users=total_users),
                graph_data=user_info)
        ), 200
