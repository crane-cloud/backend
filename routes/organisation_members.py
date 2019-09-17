from flask import request, jsonify, Blueprint

from models.organisation_members import OrganisationMembers

# custom response helper
from helpers.construct_response import *

# OrganisationMembers blueprint
organisation_members_bp = Blueprint('organisation_members', __name__)
@organisation_members_bp.route('/create/organisation_member', methods=['POST'])
def register_organisation_member(user_id, organisation_id):
    """ create organisation Member """
    
    # validate input
    if str(user_id).strip() and str(organisation_id).strip():
        organisation_member = OrganisationMembers(user_id, organisation_id)
        organisation_member.save()

        response = jsonify({
            'id': organisation_member.id,
            'user_id': organisation_member.user_id,
            'organisation_id' : organisation_member.organisation_id
        })

        response.status_code = 201
        return response
    else:
        response = jsonify({
            'message': 'Creation Failure'
        })
        response.status_code = 401
        return response
    