from flask import request, jsonify, Blueprint

from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)

from models.user import User

from helpers.token import generate_token, validate_token
from helpers.email import send_email

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

        # send verification token
        token = generate_token(user.email)
        verify_url = url_for("user.verify_email", token=token, _external=True)
        html = render_template("user/verify.html", verify_url=verify_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

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


@user_bp.route("/verify/<token>")
@jwt_required
def verify_email(token):
    try:
        email = validate_token(token)
    except:
        flash("The confirmation link is invalid or has expired.", "danger")
    user = User.query.filter_by(email=email).first_or_404()
    if user.verified:
        flash("Account already confirmed. Please login.", "success")
    else:
        user.verified = True
        db.session.add(user)
        db.session.commit()
