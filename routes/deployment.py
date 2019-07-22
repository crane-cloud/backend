from os import path

import yaml

from kubernetes import client, config, utils

from flask import request, Blueprint, jsonify

# custom response helper
from helpers.construct_response import *

#kube being our kubernetes instance
from app import extension_api

deployment_bp = Blueprint('deployment', __name__)

@deployment_bp.route('/deploy/yaml',methods = ['POST'])
#Deployment from a yaml file
def yamldeployment():
    #upload file
    with open(path.join(path.dirname(__file__), "nginx-deployment.yaml")) as f:
        dep = yaml.safe_load(f)
        resp = extension_api.create_namespaced_deployment(
            body=dep, namespace="ngin", _preload_content=False)
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
