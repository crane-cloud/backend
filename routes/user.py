from flask import request, jsonify, Blueprint
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)

from models.user import User

# user blueprint
user_bp = Blueprint("user", __name__)


@user_bp.route("/register", methods=["POST"])
def register():
    """ create new user """

    email = request.get_json()["email"]
    name = request.get_json()["name"]
    password = request.get_json()["password"]

    # validate input
    if str(email).strip() and str(password).strip():
        user = User(email, name, password)
        user.save()

        # email verification

        response = jsonify(
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "password": user.password,
                "date_created": user.date_created,
            }
        )

        response.status_code = 201

        return response


@user_bp.route("/login", methods=["POST"])
def login():
    """ user login """

    email = request.get_json()["email"]
    password = request.get_json()["password"]

    # validate input
    if str(email).strip() and str(password).strip():
        user = User.query.filter_by(email=email).first()

        if user and user.password_is_valid(password):
            """ right credentials """

            # generate access token
            access_token = user.generate_token(user.id)
            if access_token:
                response = jsonify(
                    {"access_token": access_token, "message": "login success"}
                )

                response.status_code = 200

                return response
        else:
            """ wrong credentials """

            response = jsonify({"message": "login failure"})

            response.status_code = 401

            return response


@user_bp.route("/protected", methods=["GET"])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
