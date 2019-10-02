from flask import request, jsonify, Blueprint, json

from models.namespaces import Namespace

# custom response helper
from helpers.construct_response import *

# OrganisationMembers blueprint
namespace_bp = Blueprint('namespaces', __name__)
@namespace_bp.route('/create/namespace', methods=['POST'])
def register_namespace(name, organisation_id):
    """ Add Namespace """
    
    # validate input
    if str(name).strip() and str(organisation_id).strip():
        
        namespace = Namespace(name, organisation_id)
        namespace.save()
        response = jsonify({
            'id': namespace.id,
            'name': namespace.name,
            'organisation_id' : namespace.organisation_id
        })

        response.status_code = 201
        return response
    else:
        response = jsonify({
            'message': 'Creation Failure'
        })
        response.status_code = 401
        return response
    

# Showing all available namespaces
@namespace_bp.route('/get/namespaces/<string:namespace_id>', methods=['GET'])
def get_all_organisations_namespaces(namespace_id):
    if namespace_id == "all":
        namespace = Namespace.query.all()
    else:
        namespace = Namespace.query.filter_by(id=namespace_id)
    result = []
    for name in namespace:
        result.append(name.toDict())
    response = json.dumps(result)
    return response