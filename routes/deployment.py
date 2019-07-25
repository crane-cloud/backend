from os import path

import yaml

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
    with open(path.join(path.dirname(__file__), "nginx-deployment.yaml")) as f:
        dep = yaml.safe_load(f)

        # dep_file = request.get_json()['ymal_file']
        # namespace = request.get_json()['namespace']
        namespaces = 'trial'

        resp = extension_api.create_namespaced_deployment(
            body=dep, namespace=namespaces, _preload_content=False)
        print("Deployment created. status='%s'" % str(resp.status))
        #TO DO: confliction status codes
        # print(str(resp.status))

        # if (str(resp.status) != '409'):
        #     response = construct_response(resp)
        #     response.status_code = resp.status
        # else:
        #     response = jsonify({
        #         msg: 'error'
        #     })
        #     response.status_code = 409
        response = construct_response(resp)
        return response

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