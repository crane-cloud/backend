import os
from types import SimpleNamespace
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

    # return kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api
    return SimpleNamespace(
        kube=kube,
        extension_api=extension_api,
        appsv1_api=appsv1_api,
        api_client=api_client,
        batchv1_api=batchv1_api,
        storageV1Api=storageV1Api
    )


def delete_cluster_app(kube_client, namespace, app):
    # delete deployment and service for the app
    deployment_name = f'{app.alias}-deployment'
    service_name = f'{app.alias}-service'
    deployment = kube_client.appsv1_api.read_namespaced_deployment(
        name=deployment_name,
        namespace=namespace
    )

    if deployment:
        kube_client.appsv1_api.delete_namespaced_deployment(
            name=deployment_name,
            namespace=namespace
        )

    service = kube_client.kube.read_namespaced_service(
        name=service_name,
        namespace=namespace
    )

    if service:
        kube_client.kube.delete_namespaced_service(
            name=service_name,
            namespace=namespace
        )

    # delete pvc
    # pvc_name = f'{app.alias}-pvc'

    # pvc = kube_client.kube.read_namespaced_persistent_volume_claim(
    #     name=pvc_name,
    #     namespace=namespace
    # )

    # if pvc:
    #     kube_client.kube.delete_namespaced_persistent_volume_claim(
    #         name=pvc_name,
    #         namespace=namespace
    #     )
