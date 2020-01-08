from flask import request, jsonify, Blueprint, json, abort

from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
)

from models.organisation import Organisation
from models.namespaces import Namespace
from models.organisation_members import OrganisationMembers

from routes.deployment import create_namespace, get_namespaces, delete_namespace
from routes.namespaces import register_namespace, get_all_organisations_namespaces

# custom response helper
from helpers.construct_response import *

# Organisation blueprint
organisation_bp = Blueprint('organisation', __name__)

#Create Organisation
@organisation_bp.route('/create/org', methods=['POST'])
def register_organisation(name):
    """ create new organisation """
    
    # validate input
    if str(name).strip():
        organisation = Organisation(name)
        organisation.save()

        response = {
            'id': organisation.id,
            'name': organisation.name,
            'date_created': organisation.date_created,
            'status_code': 201
        }
        return response

    response = jsonify({
        'message': 'Creation Failure'
    })
    response.status_code = 400
    return response


# Renaming an Organisation
@organisation_bp.route('/rename/organisation', methods=['POST'])
@jwt_required
def rename_organisation():
    org_name = request.get_json()["organisation_name"]
    new_name = request.get_json()["new_name"]
    current_user_id = get_jwt_identity()
    current_user = OrganisationMembers.query.filter_by(user_id = current_user_id).first_or_404()
    
    # check if current user in an admin
    if current_user.is_admin is True:
        organisation = Organisation.query.filter_by(name = org_name).first()
        if organisation:
            organisation.name = new_name
            organisation.update()
            response = jsonify({
                'message': 'Successfully Renamed'
            })
            response.status_code = 201
            return response 

        response = jsonify({
            'message': 'Organisation does not exist'
        })
        response.status_code = 404
        return response
            
    else:
        response = jsonify({
            'message': 'User is not an Admin'
        })
        response.status_code = 401
        return response 

# Deleting an Organisation
@organisation_bp.route('/delete/organisation', methods=['DELETE'])
@jwt_required
def delete_organisation():
    org_name = request.get_json()["organisation_name"]
    current_user_id = get_jwt_identity()
    current_user = OrganisationMembers.query.filter_by(user_id = current_user_id).first()
    
    # check if current user in an admin
    if current_user.is_admin is True:
        organisation = Organisation.query.filter_by(name = org_name).first()

        if organisation:
            organisation.delete()
            response = jsonify({
                'message': 'Successfully deleted'
            })
            response.status_code = 201
            return response 

        # Organisation  does not exist
        abort(404, description='Organisation does not exist') 

    else:
        response = jsonify({
            'message': 'User is not an Admin'
        })
        response.status_code = 401
        return response 

# Creating Namespace for an Organisation
@organisation_bp.route('/add/namespace', methods=['POST'])
@jwt_required
def add_namespace():
    namespace = request.get_json()['namespace']
    current_user_id = get_jwt_identity()
    current_user = OrganisationMembers.query.filter_by(user_id = current_user_id).first()
    
    # check if current user in an admin
    if current_user.is_admin is True:
        organisation_name = request.get_json()['organisation_name']

        organisation = Organisation.query.filter_by(name=organisation_name).first()
        # print(organisation.id)
        """ checking if organisation is in database """
        if organisation:
            resp = create_namespace(namespace)
            """ checking if namespaces been created """
            if(resp.status_code == 201):
                response = register_namespace(namespace, organisation.id)
                return response
            else:
                response = jsonify({
                    'message': 'Namespace Already exists'
                })    
                response.status_code = 401
                return response

        # Organisation  does not exist
        abort(404, description='Organisation does not exist')

    else:
        response = jsonify({
            'message': 'User is not an Admin'
        })
        response.status_code = 401
        return response 


# Show organisations Namespace
@organisation_bp.route('/organisation/show/namespaces', methods=['POST'])
def get_organisations_namespaces():
    org_name = request.get_json()["organisation_name"]
    organisation = Organisation.query.filter_by(name=org_name).first()
    if organisation:
        namespace_list = get_all_organisations_namespaces(organisation.id)
        return namespace_list

    # Organisation  does not exist
    abort(404, description='Organisation does not exist')


# Deleting an Organisations Namespace
@organisation_bp.route('/delete/namespace', methods=['DELETE'])
@jwt_required
def delete_organisation_namespace():
    name = request.get_json()['namespace']
    current_user_id = get_jwt_identity()
    current_user = OrganisationMembers.query.filter_by(user_id = current_user_id).first()
    
    # check if current user in an admin
    if current_user.is_admin is True:
        namespace = Namespace.query.filter_by(
            name = name).first_or_404(description='Namespace does not exist')

        if namespace is not None:
            namespace.delete()
            return delete_namespace(name)


    else:
        response = jsonify({
            'message': 'User is not an Admin'
        })
        response.status_code = 403
        return response 


# Showing all available organisations
@organisation_bp.route('/get/organisations/<string:org_id>', methods=['GET'])
def get_organisations(org_id):
    if org_id == "all":
        orgs = Organisation.query.all()
    else:
        orgs = Organisation.query.filter_by(id=org_id)
    result = []

    if orgs:
        for org in orgs:
            result.append(org.toDict())
        response = json.dumps(result)
        return response
