from flask import request, jsonify, Blueprint

from models.organisation import Organisation

# custom response helper
from helpers.construct_response import *

# Organisation blueprint
organisation_bp = Blueprint('organisation', __name__)
@organisation_bp.route('/create/organisation', methods=['POST'])
def register_organisation():
    """ create new organisation """
    name = request.get_json()['name']

    # validate input
    if str(name).strip():
        organisation = Organisation(name)
        organisation.save()

        response = jsonify({
            'id': organisation.id,
            'name': organisation.name,
            'date_created': organisation.date_created
        })

        response.status_code = 201
        return response
    else:
        response = jsonify({
            'message': 'Creation Failure'
        })
        response.status_code = 401
        return response

    