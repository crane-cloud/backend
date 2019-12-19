from flask import request, jsonify, Blueprint

from models.organisation_members import OrganisationMembers

# custom response helper
from helpers.construct_response import *

# OrganisationMembers blueprint
organisation_members_bp = Blueprint('organisation_members', __name__)

@organisation_members_bp.route('/create/organisation_member', methods=['POST'])
def register_organisation_member(user_id, organisation_id, is_admin):
    """ create organisation Member """
    
    # validate input
    if str(user_id).strip() and str(organisation_id).strip():
        organisation_member = OrganisationMembers(user_id, organisation_id, is_admin)
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

# deleting organisation member
@organisation_members_bp.route('/delete/organisation_member', methods=['POST'])
def delete_organisation_member(user_id, organisation_id):
    org_member = OrganisationMembers.query.filter_by(user_id=user_id, organisation_id =organisation_id).first()
    
    if org_member is not None: 
        org_member.delete()
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