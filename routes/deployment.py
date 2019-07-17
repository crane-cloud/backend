from os import path

from kubernetes import client, config, utils

from flask import request, Blueprint

#kube being our kubernetes instance
from app import kube

deployment_bp = Blueprint('deployment', __name__)

@deployment_bp.route('/deploy/yaml',methods = ['GET'])
#Deployment from a yaml file
def yamldeployment():
    #upload file
    #TO DO: point the upload folder to an upload file and test it. havent tested it
    UPLOAD_FOLDER = '~/Documents/yamls/1-nginx-pod.yaml'
    ALLOWED_EXTENSIONS = set(['yml','yaml','json'])
    DEPLOYMENT_NAME = "nginx-deployment"
    NAMESPACE = "default"
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    # config.load_kube_config()
    # k8s_client = client.ApiClient()
    utils.create_from_yaml(kube, UPLOAD_FOLDER)
    #k8s_api = client.ExtensionsV1beta1Api(kube)
    deps = kube.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
    print("Deployment {0} created".format(deps.metadata.name))


