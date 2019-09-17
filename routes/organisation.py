from flask import request, jsonify, Blueprint, json

from models.organisation import Organisation
from models.namespaces import Namespace

from routes.deployment import create_namespace, get_namespaces
from routes.namespaces import register_namespace

# custom response helper
from helpers.construct_response import *

# Organisation blueprint
organisation_bp = Blueprint('organisation', __name__)
@organisation_bp.route('/create/org', methods=['POST'])
def register_organisation(name):
    """ create new organisation """
    print(name)
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
    else:
        response = jsonify({
            'message': 'Creation Failure'
        })
        response.status_code = 401
        return response


# Creating Namespace for an Organisation
@organisation_bp.route('/add/namespace', methods=['POST'])
def add_namespace():
    namespace = request.get_json()['namespace']
    organisation_name = request.get_json()['organisation_name']

    organisation = Organisation.query.filter_by(name=organisation_name).first()
    # print(organisation.id)
    """ checking if organisation is in database """
    if organisation is not None:
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
    else:
        response = jsonify({
            'message': 'Organisation Does not exist'
        })
        response.status_code = 401
        return response


# Showing all available organisations
@organisation_bp.route('/get/organisations/<string:org_id>', methods=['GET'])
def get_organisations(org_id):
    if org_id == "all":
        orgs = Organisation.query.all()
    else:
        orgs = Organisation.query.filter_by(id=org_id)
    result = []
    for org in orgs:
        result.append(org.toDict())
    response = json.dumps(result)
    return response


    