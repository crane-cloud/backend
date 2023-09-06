def resource_clean_up(registry, app_alias, namespace, kube_client):
    # get a list of all created services so far
    resources = set([k for k, v in registry.items() if v])

    db_name = f'{app_alias}-postgres-db'

    if 'db_deployment' in resources:
        # delete db deployment
        try:
            kube_client.appsv1_api.delete_namespaced_deployment(
                db_name, namespace
            )
        except Exception:
            pass

    if 'db_service' in resources:
        # delete db service
        try:
            kube_client.appsv1_api.delete_namespaced_service(
                db_name, namespace
            )
        except Exception:
            pass

    if 'image_pull_secret' in resources:
        # delete image pull secret
        try:
            kube_client.kube.delete_namespaced_secret(
                app_alias, namespace
            )
        except Exception:
            pass

    if 'app_deployment' in resources:
        # delete app deployment
        name = f'{app_alias}-deployment'
        try:
            kube_client.appsv1_api.delete_namespaced_deployment(
                name, namespace
            )
        except Exception:
            pass

    if 'app_service' in resources:
        # delete app service
        name = f'{app_alias}-service'
        try:
            kube_client.kube.delete_namespaced_service(
                name, namespace
            )
        except Exception:
            pass

    # To do: Add clean up for ingress_entry
