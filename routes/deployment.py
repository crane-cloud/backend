from os import path

import yaml, base64

from kubernetes import client, config, utils

from flask import request, Blueprint, jsonify

# custom response helper
from helpers.construct_response import *

#kube being our kubernetes instance
from app import extension_api

deployment_bp = Blueprint('deployment', __name__)


#Deployment from a yaml file
@deployment_bp.route('/deploy/yaml',methods = ['POST'])
def yamldeployment():
    #upload file
    dep_file = request.get_json()['yaml_file']
    namespace = request.get_json()['namespace']
    dep_yaml = yaml.safe_load(base64.b64decode(dep_file))

    try:
        resp = extension_api.create_namespaced_deployment(
        body=dep_yaml, namespace=namespace, _preload_content=False)
        return "Deployment Successful: "+str(resp.status)

    except:
    
        return 'Error Already exits'

    # if (str(resp.status) == '201'):
    #     response = jsonify({
    #         msg: 'Deployed'
    #     })
    #     response.status_code = resp.status
    #     return response
    # elif(str(resp.status) == '409'):
    #     response = jsonify({
    #         msg: 'Deployment Exists'
    #     })
    #     response.status_code = resp.status
    #     return response
    # elif(str(resp.status) == '400'):
    #     response = jsonify({
    #         msg: 'Bad data'
    #     })
    #     response.status_code = resp.status
    #     return response
    
   


#deleting a deployment
@deployment_bp.route('/deploy/delete/<string:deployment_name>/<string:namespace>',methods = ['POST'])
def _delete_deployment(deployment_name, namespace):
    print("Deleting GKE app deployment")
    extensions_v1beta1 = client.ExtensionsV1beta1Api()
    delete_options = client.V1DeleteOptions()
    delete_options.grace_period_seconds = 0
    delete_options.propagation_policy = 'Foreground'
    try:
        api_response = extensions_v1beta1.delete_namespaced_deployment(
            name=deployment_name,
            body=delete_options,
            grace_period_seconds=2,
            # namespace="default"
            namespace = namespace)
        print("Delete deployment response:%s" % api_response)
    except Exception as e:
        print('Error '+str(e))
        raise e 