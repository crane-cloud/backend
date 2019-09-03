from flask import request, jsonify, Blueprint
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)

from models.user import User
from models.organisation_members import *
from routes.organisation import register_organisation
from routes.organisation_members import register_organisation_member

# user blueprint
user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    """ create new user """

    email = request.get_json()['email']
    name = request.get_json()['name']
    password = request.get_json()['password']

    # validate input
    if str(email).strip() and str(password).strip():
        user = User(email, name, password)
        user.save()

        response = jsonify({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'password': user.password,
            'date_created': user.date_created
        })

        response.status_code = 201

        return response

@user_bp.route('/login', methods=['POST'])
def login():
    """ user login """

    email = request.get_json()['email']
    password = request.get_json()['password']

    # validate input
    if str(email).strip() and str(password).strip():
        user = User.query.filter_by(email=email).first()

        if user and user.password_is_valid(password):
            """ right credentials """

            # generate access token
            access_token = user.generate_token(user.id)
            if access_token:
                response = jsonify({
                    'access_token': access_token,
                    'message': 'login success'
                })

                response.status_code = 200

                return response
        else:
            """ wrong credentials """

            response = jsonify({
                'message': 'login failure'
            })

            response.status_code = 401

            return response

@user_bp.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


# Creating an Organisation
@user_bp.route('/create/organisation', methods=['POST'])
def create_organisation():
    current_user = get_jwt_identity()
    if(current_user is not None):
        #new organisation
        organisation_resp = register_organisation()
        if(organisation_resp.status_code is 201):
            """ successfull """

            response = register_organisation_member(current_user, organisation_resp.id)
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






    