from os import path

from kubernetes import client, config, utils

from flask import request, Blueprint

from app import kube

deployment_bp = Blueprint('deployment', __name__)

@deployment_bp.route('/deploy/yaml',methods = ['GET'])
#Deployment from a yaml file
def yamldeployment():
    #upload file
    UPLOAD_FOLDER = '~/Documents/yamls/1-nginx-pod.yaml'
    ALLOWED_EXTENSIONS = set(['yml','yaml','json'])
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    # config.load_kube_config()
    # k8s_client = client.ApiClient()
    utils.create_from_yaml(kube, "nginx-deployment.yaml")
    k8s_api = client.ExtensionsV1beta1Api(kube)
    deps = k8s_api.read_namespaced_deployment("nginx-deployment", "default")
    print("Deployment {0} created".format(deps.metadata.name))
