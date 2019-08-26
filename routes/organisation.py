from flask import request, jsonify, Blueprint

from models.organisation import Organisation

# custom response helper
from helpers.construct_response import *

# admin blueprint
organisation_bp = Blueprint('organisation', __name__)
@organisation_bp.route('/create/organisation', methods=['POST'])
def register():
    """ create new organisation """
    name = request.get_json()['name']
    namespace = request.get_json()['namespace']
    member = request.get_json()['member']

    # validate input
    if str(name).strip() and str(namespace).strip() and str(member).strip:
        organisation = Organisation(name, namespace, member)
        organisation.save()

        response = jsonify({
            'id': organisation.id,
            'name': organisation.name,
            'namespace': organisation.namespace,
            'member': organisation.member,
            'date_created': organisation.date_created
        })

        response.status_code = 201
        return response

    