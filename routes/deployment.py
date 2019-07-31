from os import path

import yaml, base64, logging

from kubernetes import client, config, utils

from flask import request, Blueprint, jsonify

# custom response helper
from helpers.construct_response import *

#kube being our kubernetes instance
from app import extension_api, kube

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

    except client.rest.ApiException as e:
        logging.exception(e)
        return 'Error Already exits {}'.format(e)

    
#deleting a deployment
@deployment_bp.route('/deploy/delete/<string:deployment_name>/<string:namespace>',methods = ['POST'])
def delete_deployment(deployment_name, namespace):
    try:
        api_response = extension_api.delete_namespaced_deployment(name=deployment_name, namespace = namespace, async_req=False)
        print("Deleted deployment response:%s" % api_response)
        logging.info('deleted deployment /{} from {} namespace'.format(deployment_name, namespace))
        return 'deleted deployment {} from {} namespace'.format(deployment_name, namespace) 
    except client.rest.ApiException as e:
        logging.exception(e)
        return "Error: {}".format(e)
   

#Creating namespace
@deployment_bp.route('/deploy/create/namespace/<string:namespace>', methods = ['POST'])
def create_namespace(namespace):
    try:
        resp = kube.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace)))
        return "Namespace created: "+format(resp.status)
    except client.rest.ApiException as e:
        logging.exception(e)
        return "Error: {} /n".format(e)
        
    else:
        logging.info('created /{} namespace'.format(namespace))
        return 'created /{} namespace'.format(namespace)
        
# Deleting namespace
@deployment_bp.route('/deploy/delete/namespace/<string:namespace>', methods = ['POST'])
def delete_namespace(namespace):
    try:
        resp = kube.delete_namespace(namespace)
        return "Namespace Deleted: "+str(resp.status)
    except client.rest.ApiException as e:
        logging.exception(e)
        return "Error: {}".format(e)
        
    else:
        logging.info('Deleted {} namespace'.format(namespace))
        return 'Deleted {} namespace'.format(namespace)

