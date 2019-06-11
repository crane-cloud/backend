from flask import request, jsonify, Blueprint

from app import kube

# admin blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/pods/', methods=['GET'])
def get_pods():
    pods = kube.list_pod_for_all_namespaces(watch=False)

    response = jsonify({
        'pods': str(pods.items)
    })

    response.status_code = 200
    
    return response

@admin_bp.route('/resources/', methods=['GET'])
def get_resources():
    resources = kube.get_api_resources()

    response = jsonify({
        'resources': str(resources.resources)
    })

    response.status_code = 200
    
    return response