import os
# import kubernetes client
from kubernetes import client


def create_kube_clients(kube_host=os.getenv('KUBE_HOST'), kube_token=os.getenv('KUBE_TOKEN')):
    # configure client
    config = client.Configuration()
    config.host = kube_host
    config.api_key['authorization'] = kube_token
    config.api_key_prefix['authorization'] = 'Bearer'
    config.verify_ssl = False
    # config.assert_hostname = False

    # create API instance
    api_client = client.ApiClient()
    kube = client.CoreV1Api(client.ApiClient(config))
    extension_api = client.ExtensionsV1beta1Api(client.ApiClient(config))
    appsv1_api = client.AppsV1Api(client.ApiClient(config))
    batchv1_api = client.BatchV1Api(client.ApiClient(config))
    storageV1Api = client.StorageV1Api(client.ApiClient(config))

    return kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api
