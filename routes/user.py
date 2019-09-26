from flask import request, jsonify, Blueprint
import json
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
from models.user import User
from models.organisation_members import *
from models.organisation import *
from routes.organisation import register_organisation, get_organisations
from routes.organisation_members import register_organisation_member

# user blueprint
user_bp = Blueprint("user", __name__)

#  User registration
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

# User Login
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


# Delete User account
@user_bp.route('/delete/user', methods=['DELETE'])
def delete_user_account():
    user_id = request.get_json()['user_id']
    user = User.query.filter_by(id = user_id).first()
    
    if user is not None:
        user.delete()
        response = jsonify({
            'message': 'Successfully deleted'
        })
        response.status_code = 201
        return response 
    else:
        response = jsonify({
            'message': 'User does not exist'
        })
        response.status_code = 401
        return response 

# Creating an Organisation
@user_bp.route('/create/organisation', methods=['POST'])
@jwt_required
def create_organisation():
    current_user = get_jwt_identity()
    org_name = request.get_json()['org_name']
    if(current_user is not None):
        """ Register the organisation """

        organisation_resp = register_organisation(org_name)
        
        if(organisation_resp['status_code'] == 201):
            """ Register them into the association table """
            response = register_organisation_member(current_user, organisation_resp['id'])
            return response
        else:
            response = jsonify({
                'message': 'Organisation failure'
            })
            response.status_code = 401
            return response
    else:
        response = jsonify({
                'message': 'Current user not authorised'
        })
        response.status_code = 401
        return response


# Adding a member to an organisation
@user_bp.route('/add/member', methods=['POST'])
def add_member():
    email = request.get_json()['email']
    organisation_name = request.get_json()['organisation_name']
    user = User.query.filter_by(email=email).first()
    organisation = Organisation.query.filter_by(name=organisation_name).first()
    
    if user and organisation_name: 
        response = register_organisation_member(user.id, organisation.id)
        return response
    else:
        """Send a link to user """
        pass


# Show organisations list
@user_bp.route('/user/get/organisations', methods=['GET'])
@jwt_required
def get_organisation():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if user is not None:
        org_association = OrganisationMembers.query.filter_by(user_id=user.id).all()
        repsArr = []

        for i in org_association:
            dict_obj = i.toDict()
            organisation = get_organisations(dict_obj["organisation_id"])
            organisation = json.loads(organisation)
            if len(organisation) > 0:
                repsArr.append(organisation[0])

        response = json.dumps(repsArr)
        return response
    else:
        response = jsonify({
            "message": "Not registered user"
        })
        return response