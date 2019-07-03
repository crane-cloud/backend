from flask import request, Blueprint
from prometheus_http_client import Prometheus

#initialise prometheus
prometheus = Prometheus()

#monitor Blueprint
monitor_bp = Blueprint('monitor', __name__)

#Cluster info
@monitor_bp.route('/monitor/cluster/pod',methods=['GET'])
def get_cluster_Pod_usage():
    return prometheus.query(metric='sum(kube_pod_info{node=~".*"}) / sum(kube_node_status_allocatable_pods{node=~".*"})')
    
@monitor_bp.route('/monitor/cluster/cpu',methods=['GET'])
def get_cluster_CPU_usage():
    return prometheus.query(metric='sum(kube_pod_container_resource_requests_cpu_cores{node=~".*"}) / sum(kube_node_status_allocatable_cpu_cores{node=~".*"})')

@monitor_bp.route('/monitor/cluster/memory',methods=['GET'])
def get_cluster_Memory_usage():
    return prometheus.query(metric='sum(kube_pod_container_resource_requests_memory_bytes{node=~".*"}) / sum(kube_node_status_allocatable_memory_bytes{node=~".*"})')

@monitor_bp.route('/monitor/cluster/disk',methods=['GET'])
def get_cluster_Disk_usage():
    return prometheus.query(metric='(sum (node_filesystem_size_bytes{nodename=~".*"}) - sum (node_filesystem_free_bytes{nodename=~".*"})) / sum (node_filesystem_size_bytes{nodename=~".*"})')


#Deployment info
@monitor_bp.route('/monitor/deployment/replicas/info',methods=['GET'])
def get_deployment_replicas():
    return prometheus.query(metric='kube_deployment_status_replicas{namespace=~".*"}')

@monitor_bp.route('/monitor/deployment/replicas/',methods=['GET'])
def get_no_replicas():
    return prometheus.query(metric='sum(kube_deployment_status_replicas{namespace=~".*"})')

@monitor_bp.route('/monitor/deployment/repupdated',methods=['GET'])
def get_no_replicas_apdated():
    return prometheus.query(metric='sum(kube_deployment_status_replicas_updated{namespace=~".*"})')

@monitor_bp.route('/monitor/deployment/repunavailable',methods=['GET'])
def get_no_replicas_unavailable():
    return prometheus.query(metric='sum(kube_deployment_status_replicas_unavailable{namespace=~".*"})')


#Node info
@monitor_bp.route('/monitor/nodes',methods=['GET'])
def get_no_nodes():
    return prometheus.query(metric='sum(kube_node_info{node=~".*"})')

@monitor_bp.route('/monitor/nodes/outofdisk',methods=['GET'])
def get_nodes_out_Of_Disk():
    return prometheus.query(metric='sum(kube_node_status_condition{condition="OutOfDisk", node=~".*", status="true"})')

@monitor_bp.route('/monitor/nodes/unavailable',methods=['GET'])
def get_nodes_unavailable():
    return prometheus.query(metric='sum(kube_node_spec_unschedulable)')

@monitor_bp.route('/monitor/nodes/info',methods=['GET'])
def get_nodes_info():
    return prometheus.query(metric='kube_node_info{node=~".*"}')


#pod info
@monitor_bp.route('/monitor/pods',methods=['GET'])
def get_pods_running():
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~".*", phase="Running"})')
 
@monitor_bp.route('/monitor/pods/pending',methods=['GET'])
def get_pods_pending():
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~".*", phase="Pending"})')

@monitor_bp.route('/monitor/pods/failed',methods=['GET'])
def get_pods_failed():
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~".*", phase="Failed"})')

@monitor_bp.route('/monitor/pods/succeeded',methods=['GET'])
def get_pods_succeeded():
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~".*", phase="Succeeded"})')


#Container info
@monitor_bp.route('/monitor/containers',methods=['GET'])
def get_containers_running():
    return prometheus.query(metric='sum(kube_pod_container_status_running{namespace=~".*"})')

@monitor_bp.route('/monitor/containers/waiting',methods=['GET'])
def get_containers_waiting():
    return prometheus.query(metric='sum(kube_pod_container_status_waiting{namespace=~".*"})')
 
@monitor_bp.route('/monitor/containers/terminated',methods=['GET'])
def get_containers_terminated():
    return prometheus.query(metric='sum(kube_pod_container_status_terminated{namespace=~".*"})')

@monitor_bp.route('/monitor/containers/restarts',methods=['GET'])
def get_containers_restarts():
    return prometheus.query(metric='sum(delta(kube_pod_container_status_restarts_total{namespace="kube-system"}[30m]))')

@monitor_bp.route('/monitor/containers/cpu',methods=['GET'])
def get_containers_cpu_cores_requested():
    return prometheus.query(metric='sum(kube_pod_container_resource_requests_cpu_cores{namespace=~".*", node=~".*"})')

@monitor_bp.route('/monitor/coontainers/memory',methods=['GET'])
def get_containers_memory_requested():
    return prometheus.query(metric='sum(kube_pod_container_resource_requests_memory_bytes{namespace=~".*", node=~".*"})')


#Jobs info
@monitor_bp.route('/monitor/jobs/suceeded',methods=['GET'])
def get_jobs_succeeded():
    return prometheus.query(metric='sum(kube_job_status_succeeded{namespace=~".*"})')

@monitor_bp.route('/monitor/job/failed',methods=['GET'])
def get_failed():
    return prometheus.query(metric='sum(kube_job_status_failed{namespace=~".*"})')


