

from app.models.app import AppState

from app.models.clusters import Cluster
from app.models.project import Project
from app.models.app import App
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


def update_or_create_app_state(app_status_message):

    app_id = app_status_message["app"]
    existing_state = AppState.find_first(app=app_id)
    if existing_state:
        # Update existing entry
        existing_state.failure_reason = app_status_message.get(
            "failure_reason", None)
        existing_state.message = app_status_message["message"]
        existing_state.status = app_status_message["status"]
        existing_state.last_check = app_status_message.get(
            "last_check", datetime.now())
    else:
        # Create new entry
        new_state = AppState(
            app=app_id,
            failure_reason=app_status_message.get("failure_reason", None),
            message=app_status_message["message"],
            status=app_status_message["status"],
            last_check=app_status_message.get("last_check", datetime.now())
        )
        new_state.save()


def check_app_statuses():
    from app.helpers.kube import create_kube_clients
    projects = Project.query.all()
    db = SQLAlchemy()
    db.create_all()
    # Iterate over each project
    for project in projects:
        print(f"Project ID: {project.id}, Name: {project.name}")

        apps = App.query.filter_by(project_id=project.id).all()

        cluster = Cluster.get_by_id(str(project.cluster_id))

        for app in apps:
            print(f"App ID: {app.id}, Name: {app.name}")

            if app.disabled:
                update_or_create_app_state({
                    "app": app.id,
                    "status": "failed",
                    "message": f"Application is disabled",
                    "failure_reason": "Disabled",
                    "last_check": datetime.now()
                })
                continue

            if not cluster:
                update_or_create_app_state({
                    "app": app.id,
                    "status": "failed",
                    "message": f"Application not connected to cluster",
                    "failure_reason": "Cluster Connection failed",
                    "last_check": datetime.now()
                })
                continue

            try:
                kube_host = cluster.host
                kube_token = cluster.token
                kube_client = create_kube_clients(kube_host, kube_token)

            except Exception as e:
                print(e)
                update_or_create_app_state({
                    "app": app.id,
                    "status": "failed",
                    "message": f"Failed to connect to cluster with the application",
                    "failure_reason": "Cluster Connection failed",
                    "last_check": datetime.now()
                })
                continue

            pods = kube_client.kube.list_namespaced_pod(project.alias).items

            replicas = kube_client.appsv1_api.list_namespaced_replica_set(
                project.alias).to_dict()
            replicasList = []

            for replica in replicas['items']:
                name = replica['metadata']['name']
                if name.startswith(app.alias):
                    replicasList.append(name)

            podsList = []
            for item in pods:
                item = kube_client.api_client.sanitize_for_serialization(item)
                pod_name = item['metadata']['name']
                # to avoid repetition
                added = False
                for replica in replicasList:
                    if pod_name.startswith(replica):
                        podsList.append(item)
                        added = True
                        continue
                if pod_name.startswith(app.alias) and not added:
                    podsList.append(item)
                    continue

            custom_app_message = {
                "app": app.id,
                "last_check": datetime.now(),
                "status": "failed",
                "message": "",
                "failure_reason": ""
            }
            for index, pod_log in enumerate(podsList):
                pod_name = pod_log["metadata"]["name"]
                pod_status = pod_log["status"]["phase"]

                if pod_status == "Running":
                    custom_app_message["status"] = "running"
                    custom_app_message["message"] += f"pod:{
                        index} - is running.\n"
                else:
                    container_statuses = pod_log["status"].get(
                        "containerStatuses", [])
                    if container_statuses:
                        for container_status in container_statuses:
                            reason = container_status["state"]["waiting"]["reason"]
                            message = container_status["state"]["waiting"]["message"]
                            # Add message with newline
                            custom_app_message["message"] += f"pod:{
                                index} - down, Message:{message}."
                            custom_app_message["failure_reason"] += f"pod:{
                                index} - {reason}."
                    else:
                        custom_app_message["message"] += f"Failed to access pod:{
                            index} status. "
                        custom_app_message["failure_reason"] += f"pod:{
                            index} - Unknown. "

            update_or_create_app_state(custom_app_message)
    return True
