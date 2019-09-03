from flask import request, jsonify, Blueprint

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
    