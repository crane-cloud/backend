from os import path

import yaml, base64, logging, json

from kubernetes import client, config, utils

from flask import request, Blueprint, jsonify

from routes.monitoring import prometheus

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

# Deployment from a form
@deployment_bp.route('/deploy/form',methods = ['POST'])
def create_deployment_object():
    # Configure Pod template container
    container = client.V1Container(
        name="nginx",
        image="nginx:1.15.4",
        ports=[client.V1ContainerPort(container_port=80)])
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "nginx"}),
        spec=client.V1PodSpec(containers=[container]))
    # Create the specification of deployment
    spec = client.V1DeploymentSpec(
        replicas=3,
        template=template,
        selector={'matchLabels': {'app': 'nginx'}})
    # Instantiate the deployment object
    try:
        deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name="nginx"),
        spec=spec)
        return 'SuccessFull'
    except client.rest.ApiException as e:
        logging.exception(e)
        return "Error: {}".format(e)

       
    
#deleting a deployment
@deployment_bp.route('/deploy/delete/deployment/<string:deployment_name>/<string:namespace>',methods = ['POST'])
def delete_deployment(deployment_name, namespace):
    try:
        api_response = extension_api.delete_namespaced_deployment(name=deployment_name, namespace = namespace, async_req=False)
        print("Deleted deployment response:%s" % api_response)
        logging.info('deleted deployment /{} from {} namespace'.format(deployment_name, namespace))
        return 'deleted deployment {} from {} namespace'.format(deployment_name, namespace) 
    except client.rest.ApiException as e:
        logging.exception(e)
        return "Error: {}".format(e)

#Watch deployments pods
@deployment_bp.route('/deploy/deployment/pods/',methods = ['GET'])
def watch_pod_deployment():
    resp = kube.list_pod_for_all_namespaces(watch=False)
    return resp


#Getting namespaces
@deployment_bp.route('/deploy/get/namespaces', methods = ['GET'])
def get_namespaces():
        resp = kube.list_namespace()
        namlist = [i.metadata.name for i in resp.items]
        response = jsonify({
            'name': namlist
        })
        response.status_code = 200
        return response

   

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

# Showing pod status
@deployment_bp.route('/deploy/show/pods/<string:namespace>',methods=['GET'])
def get_cluster_Pod_usage(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='kube_pod_info{namespace=~"'+namespace+'"}')



##TODO: test the following

@deployment_bp.route('/deploy/update/service/<string:deployment_name>/<string:namespace>',methods = ['POST'])
def update_service(service_object):
    #upload file
    encoded_file = request.get_json()['yaml_file']
    namespace = request.get_json()['namespace']
    yaml_object = yaml.safe_load(base64.b64decode(encoded_file))
    name = yaml_object.metadata.name
    if namespace is None:
        namespace = service_object.metadata.namespace

    try:
        service = kube.patch_namespaced_service(name, namespace, yaml_object)
    except client.rest.ApiException as e:
        logging.exception(e)
        return e
    else:
        logging.info('updated svc/{} in ns/{}'.format(name, namespace))
        return 'updated svc/{} from ns/{}'.format(name, namespace)

#deleting a service
@deployment_bp.route('/deploy/delete/service/<string:service_name>/<string:namespace>', methods = ['POST'])
def delete_service(service_name, namespace):
    try:
        resp = kube.delete_namespaced_service(service_name, namespace)
        return "Service Deleted: " +str(resp.status)
    except client.rest.ApiException as e:
        logging.exception(e)
        return "Error: {}".format(e)
    else:
        logging.info('deleted svc/{} from ns/{}'.format(service_name, namespace))
        return 'deleted svc/{} from ns/{}'.format(service_name, namespace)
