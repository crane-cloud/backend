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
    # extension_api = client.ExtensionsV1beta1Api(client.ApiClient(config))
    appsv1_api = client.AppsV1Api(client.ApiClient(config))
    batchv1_api = client.BatchV1Api(client.ApiClient(config))
    storageV1Api = client.StorageV1Api(client.ApiClient(config))
    networking_api = client.NetworkingV1Api(client.ApiClient(config))

    # return kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api
    return SimpleNamespace(
        kube=kube,
        # extension_api=extension_api,
        networking_api=networking_api,
        appsv1_api=appsv1_api,
        api_client=api_client,
        batchv1_api=batchv1_api,
        storageV1Api=storageV1Api
    )


def delete_cluster_app(kube_client, namespace, app):
    # delete deployment and service for the app

    deployment_name = f'{app.alias}-deployment'
    service_name = f'{app.alias}-service'
    try:

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

        secret = kube_client.kube.read_namespaced_secret(
            name=app.alias,
            namespace=namespace
        )
        kube_client.kube.delete_namespaced_secret(
            name=app.alias,
            namespace=namespace
        )
    except Exception as e:
        if e.status != 404:
            return dict(status='fail', message=str(e)), 500

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


def get_status(success, failed):
    if failed == 0:
        return 'success'
    elif success == 0:
        return 'failed'
    else:
        return 'partial'


def get_kube_cluster_status(kube_client):
    # get cluster status
    try:
        cluster_status_list = kube_client.kube.list_component_status()
        cluster_status = []
        success = 0
        failed = 0
        for cluster_status_list_item in cluster_status_list.items:
            kubelet_status = cluster_status_list_item.conditions[0]
            cluster_status.append({
                'name': cluster_status_list_item.metadata.name,
                'status': kubelet_status.status,
                'type': kubelet_status.type,
                'error': kubelet_status.error
            })
            success += 1 if kubelet_status.status == 'True' else 0
            failed += 1 if kubelet_status.status == 'False' else 0

    # cluster_status = kube_client.kube.read_component_status()
        return {'status': get_status(success, failed),
                'data': cluster_status}
    except Exception:
        return {
            'status': 'failed',
            'data': []
        }


def get_cluster_status_info(clusters):
    clusters_status = []
    for cluster in clusters:
        kube_host = cluster.host
        kube_token = cluster.token

        kube_client = create_kube_clients(kube_host, kube_token)
        status = get_kube_cluster_status(kube_client)
        clusters_status.append({
            'cluster_name': cluster.name,
            'status': status['status'],
            'cluster_status': status['data']
        })
    return clusters_status
