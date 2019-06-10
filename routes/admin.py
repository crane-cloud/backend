from flask import request, jsonify

from app import app, api

@app.route('/pods/', methods=['GET'])
def get_pods():
    pods = api.list_pod_for_all_namespaces(watch=False)

    response = jsonify({
        'list': str(pods.items)
    })

    response.status_code = 200
    
    return response