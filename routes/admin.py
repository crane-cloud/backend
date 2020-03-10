from flask import request, Blueprint

from app import kube

# custom response helper
from helpers.construct_response import *

# admin blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/pods/', methods=['GET'])
def get_pods():
    """ list pods for all namespaces """
    
    pods = kube.list_pod_for_all_namespaces(watch=False, _preload_content=False).read()

    response = construct_response(pods)
    response.status_code = 200

    return response

@admin_bp.route('/resources/', methods=['GET'])
def get_resources():
    """ get available resources """

    resources = kube.get_api_resources(_preload_content=False).read()

    response = construct_response(resources)
    response.status_code = 200

    return response