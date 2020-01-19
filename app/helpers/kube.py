import os
# import kubernetes client
from kubernetes import client

# configure client
config = client.Configuration()
config.host = os.getenv('KUBE_HOST')
config.api_key['authorization'] = os.getenv('KUBE_TOKEN')
config.api_key_prefix['authorization'] = 'Bearer'
config.verify_ssl = False
# config.assert_hostname = False

# create API instance
api_client = client.ApiClient()
kube = client.CoreV1Api(client.ApiClient(config))
extension_api = client.ExtensionsV1beta1Api(client.ApiClient(config))
appsv1_api = client.AppsV1Api(client.ApiClient(config))
