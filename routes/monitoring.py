from flask import request, Blueprint
from prometheus_http_client import Prometheus

#initialise prometheus
prometheus = Prometheus()

#monitor Blueprint
monitor_bp = Blueprint('monitor', __name__)

# #Cluster info
# @monitor_bp.route('/monitor/cluster/pod',methods=['GET'])
# def get_cluster_Pod_usage():
#     return prometheus.query(metric='sum(kube_pod_info{node=~".*"}) / sum(kube_node_status_allocatable_pods{node=~".*"})')
    
# @monitor_bp.route('/monitor/cluster/cpu',methods=['GET'])
# def get_cluster_CPU_usage():
#     return prometheus.query(metric='sum(kube_pod_container_resource_requests_cpu_cores{node=~".*"}) / sum(kube_node_status_allocatable_cpu_cores{node=~".*"})')

# @monitor_bp.route('/monitor/cluster/memory',methods=['GET'])
# def get_cluster_Memory_usage():
#     return prometheus.query(metric='sum(kube_pod_container_resource_requests_memory_bytes{node=~".*"}) / sum(kube_node_status_allocatable_memory_bytes{node=~".*"})')

# @monitor_bp.route('/monitor/cluster/disk',methods=['GET'])
# def get_cluster_Disk_usage():
#     return prometheus.query(metric='(sum (node_filesystem_size_bytes{nodename=~".*"}) - sum (node_filesystem_free_bytes{nodename=~".*"})) / sum (node_filesystem_size_bytes{nodename=~".*"})')


# #Node info
# @monitor_bp.route('/monitor/nodes/',methods=['GET'])
# def get_no_nodes():
#     return prometheus.query(metric='sum(kube_node_info{node=~".*"})')

# @monitor_bp.route('/monitor/nodes/outofdisk',methods=['GET'])
# def get_nodes_out_Of_Disk():
#     return prometheus.query(metric='sum(kube_node_status_condition{condition="OutOfDisk", node=~".*", status="true"})')

# @monitor_bp.route('/monitor/nodes/unavailable',methods=['GET'])
# def get_nodes_unavailable():
#     return prometheus.query(metric='sum(kube_node_spec_unschedulable)')

# @monitor_bp.route('/monitor/nodes/info',methods=['GET'])
# def get_nodes_info():
#     return prometheus.query(metric='kube_node_info{node=~".*"}')


# #Deployment info
# @monitor_bp.route('/monitor/deployment/replicas/info/<string:namespace>',methods=['GET'])
# def get_deployment_replicas(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='kube_deployment_status_replicas{namespace=~"'+namespace+'"}')

# @monitor_bp.route('/monitor/deployment/replicas/<string:namespace>',methods=['GET'])
# def get_no_replicas(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_deployment_status_replicas{namespace=~"'+namespace+'"})')

# @monitor_bp.route('/monitor/deployment/repupdated/<string:namespace>',methods=['GET'])
# def get_no_replicas_apdated(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_deployment_status_replicas_updated{namespace=~"'+namespace+'"})')

# @monitor_bp.route('/monitor/nodes/<string:namespace>',methods=['GET'])
# def get_no_replicas_unavailable(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_deployment_status_replicas_unavailable{namespace=~"'+namespace+'"})')


# #pod info
# @monitor_bp.route('/monitor/pods/<string:namespace>',methods=['GET'])
# def get_pods_running(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Running"})')
 
# @monitor_bp.route('/monitor/pods/pending/<string:namespace>',methods=['GET'])
# def get_pods_pending(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Pending"})')

# @monitor_bp.route('/monitor/pods/failed/<string:namespace>',methods=['GET'])
# def get_pods_failed(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Failed"})')

# @monitor_bp.route('/monitor/pods/succeeded/<string:namespace>',methods=['GET'])
# def get_pods_succeeded(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Succeeded"})')


# #Container info
# @monitor_bp.route('/monitor/containers/<string:namespace>',methods=['GET'])
# def get_containers_running(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_container_status_running{namespace=~"'+namespace+'"})')


# @monitor_bp.route('/monitor/containers/wainting/<string:namespace>',methods=['GET'])
# def get_containers_waiting(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_container_status_waiting{namespace=~"'+namespace+'"})')
 
# @monitor_bp.route('/monitor/containers/terminated/<string:namespace>',methods=['GET'])
# def get_containers_terminated(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_container_status_terminated{namespace=~"'+namespace+'"})')

# @monitor_bp.route('/monitor/containers/restarts/<string:namespace>',methods=['GET'])
# def get_containers_restarts(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(delta(kube_pod_container_status_restarts_total{namespace=~"'+namespace+'"}[30m]))')

# @monitor_bp.route('/monitor/containers/cpu/<string:namespace>',methods=['GET'])
# def get_containers_cpu_cores_requested(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_container_resource_requests_cpu_cores{namespace=~"'+namespace+'", node=~".*"})')

# @monitor_bp.route('/monitor/coontainers/memory/<string:namespace>',methods=['GET'])
# def get_containers_memory_requested(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_pod_container_resource_requests_memory_bytes{namespace=~"'+namespace+'", node=~".*"})')


# #Jobs info
# @monitor_bp.route('/monitor/jobs/succeeded/<string:namespace>',methods=['GET'])
# def get_jobs_succeeded(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_job_status_succeeded{namespace=~"'+namespace+'"})')

# @monitor_bp.route('/monitor/job/failed/<string:namespace>',methods=['GET'])
# def get_failed(namespace):
#     if (namespace == 'all'):
#         namespace = '.*'
#     return prometheus.query(metric='sum(kube_job_status_failed{namespace=~"'+namespace+'"})')


