import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import UserSchema
from app.models.user import User


class UsersView(Resource):

    def post(self):
        """
        """

        user_schema = UserSchema()

        user_data = request.get_json()

        validated_user_data, errors = user_schema.load(user_data)

        email = validated_user_data.get('email', None)

        if errors:
            return dict(status="fail", message=errors), 400

        user_existant = User.query.filter_by(email=email).first()

        if user_existant:
            return dict(status="fail", message=f"Email {validated_user_data['email']} already in use."), 400

        user = User(**validated_user_data)
        saved_user = user.save()

        if not saved_user:
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_user_data, errors = user_schema.dumps(user)

        return dict(status='success', data=dict(user=json.loads(new_user_data))), 201

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

        user_schema = UserSchema(only=("email", "password"))

        login_data = request.get_json()

        validated_user_data, errors = user_schema.load(login_data)

        if errors:
            return dict(status='fail', message=errors), 400

        email = validated_user_data.get('email', None)
        password = validated_user_data.get('password', None)

        user = User.find_first(email=email)

        if user and user.password_is_valid(password):

            access_token = user.generate_token(user.id)

            if not access_token:
                return dict(status="fail", message="Unable to generate token"), 401

            return dict(status='success', data=dict(acess_token=access_token)), 200

        return dict(status='fail', message="login failed"), 401
