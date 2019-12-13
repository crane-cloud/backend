from flask import request, Blueprint,jsonify
from prometheus_http_client import Prometheus
import json

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


#Node info
@monitor_bp.route('/monitor/nodes/',methods=['GET'])
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


#Deployment info
@monitor_bp.route('/monitor/deployment/replicas/info/<string:namespace>',methods=['GET'])
def get_deployment_replicas(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='kube_deployment_status_replicas{namespace=~"'+namespace+'"}')

@monitor_bp.route('/monitor/deployment/replicas/<string:namespace>',methods=['GET'])
def get_no_replicas(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_deployment_status_replicas{namespace=~"'+namespace+'"})')

@monitor_bp.route('/monitor/deployment/repupdated/<string:namespace>',methods=['GET'])
def get_no_replicas_apdated(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_deployment_status_replicas_updated{namespace=~"'+namespace+'"})')

@monitor_bp.route('/monitor/nodes/<string:namespace>',methods=['GET'])
def get_no_replicas_unavailable(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_deployment_status_replicas_unavailable{namespace=~"'+namespace+'"})')

#Monitoring deployment 


#get percentage memory usage for deployment
@monitor_bp.route('/monitor/deployment/percentage_memory_usage/<string:deployment>',methods=['GET'])
def get_deployment_percmemoryusage(deployment):
    if (deployment == 'all'):
        deployment = '.*'
    return prometheus.query(metric='sum (container_memory_working_set_bytes{pod_name=~"'+deployment+'.*"}) / sum (machine_memory_bytes{kubernetes_io_hostname=~".*"}) * 100')

#deployment memory used raw figure
@monitor_bp.route('/monitor/deployment/memory_used/<string:deployment>',methods=['GET'])
def get_deployment_memoryused(deployment):
    if (deployment == 'all'):
        deployment = '.*'
    return prometheus.query(metric='sum (container_memory_usage_bytes{pod_name=~"'+deployment+'.*"})/1024^3')

#get percentage cpu usage for deployment
@monitor_bp.route('/monitor/deployment/percentage_cpu_usage/<string:deployment>',methods=['GET'])
def get_deployment_perccpuusage(deployment):
    if (deployment == 'all'):
        deployment = '.*'
    return prometheus.query(metric='sum (rate (container_cpu_usage_seconds_total{pod_name=~"'+deployment+'.*",container_name!="POD"}[2m]))')

#deployment cpu usage for deployment raw figure
@monitor_bp.route('/monitor/deployment/cpu_used/<string:deployment>',methods=['GET'])
def get_deployment_cpuused(deployment):
    if (deployment == 'all'):
        deployment = '.*'
    return prometheus.query(metric='sum (rate(container_cpu_usage_seconds_total{pod_name=~"'+deployment+'.*"}[3m]))')


#get available replicas of a deployment
@monitor_bp.route('/monitor/deployment/replicas_available/<string:deployment>',methods=['GET'])
def get_deployment_replicas_available(deployment):
    if (deployment == 'all'):
        deployment = '.*'
    return prometheus.query(metric='sum(kube_deployment_status_replicas_available{deployment=~"'+deployment+'",pod_template_hash=""})')

# get all replicas of a deployment
@monitor_bp.route('/monitor/deployment/replicas_total/<string:deployment>',methods=['GET'])
def get_deployment_replicas_total(deployment):
    if (deployment == 'all'):
        deployment = '.*'
    return prometheus.query(metric='sum(kube_deployment_status_replicas{deployment=~"'+deployment+'",pod_template_hash=""})')

@monitor_bp.route('/monitor/deployment/infomation/<string:deployment>',methods=['GET'])
def dep(deployment):
    mem = get_deployment_memoryused(deployment)
    cpu = get_deployment_cpuused(deployment)
    availb_replicas = get_deployment_replicas_available(deployment)
    tot_replicas = get_deployment_replicas_total(deployment)

    # change to dicts
    mem = json.loads(mem)
    cpu = json.loads(cpu)
    availb_replicas = json.loads(availb_replicas)
    tot_replicas = json.loads(tot_replicas)

    response = jsonify({
         "memory": mem,
         "cpuCycles":cpu,
         "replicasAvailable":availb_replicas,
         "totReplicas":tot_replicas
            })
    
    response.status_code = 200
    return response





#pod info
@monitor_bp.route('/monitor/pods/<string:namespace>',methods=['GET'])
def get_pods_running(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Running"})')
 
@monitor_bp.route('/monitor/pods/pending/<string:namespace>',methods=['GET'])
def get_pods_pending(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Pending"})')

@monitor_bp.route('/monitor/pods/failed/<string:namespace>',methods=['GET'])
def get_pods_failed(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Failed"})')

@monitor_bp.route('/monitor/pods/succeeded/<string:namespace>',methods=['GET'])
def get_pods_succeeded(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_status_phase{namespace=~"'+namespace+'", phase="Succeeded"})')


#Container info
@monitor_bp.route('/monitor/containers/<string:namespace>',methods=['GET'])
def get_containers_running(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_container_status_running{namespace=~"'+namespace+'"})')


@monitor_bp.route('/monitor/containers/wainting/<string:namespace>',methods=['GET'])
def get_containers_waiting(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_container_status_waiting{namespace=~"'+namespace+'"})')
 
@monitor_bp.route('/monitor/containers/terminated/<string:namespace>',methods=['GET'])
def get_containers_terminated(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_container_status_terminated{namespace=~"'+namespace+'"})')

@monitor_bp.route('/monitor/containers/restarts/<string:namespace>',methods=['GET'])
def get_containers_restarts(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(delta(kube_pod_container_status_restarts_total{namespace=~"'+namespace+'"}[30m]))')

@monitor_bp.route('/monitor/containers/cpu/<string:namespace>',methods=['GET'])
def get_containers_cpu_cores_requested(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_container_resource_requests_cpu_cores{namespace=~"'+namespace+'", node=~".*"})')

@monitor_bp.route('/monitor/coontainers/memory/<string:namespace>',methods=['GET'])
def get_containers_memory_requested(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_pod_container_resource_requests_memory_bytes{namespace=~"'+namespace+'", node=~".*"})')


#Jobs info
@monitor_bp.route('/monitor/jobs/succeeded/<string:namespace>',methods=['GET'])
def get_jobs_succeeded(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_job_status_succeeded{namespace=~"'+namespace+'"})')

@monitor_bp.route('/monitor/job/failed/<string:namespace>',methods=['GET'])
def get_failed(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='sum(kube_job_status_failed{namespace=~"'+namespace+'"})')

#Config Maps info

@monitor_bp.route('/monitor/config-maps/<string:namespace>',methods=['GET'])
def get_configmaps(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='kube_configmap_created{namespace=~"'+namespace+'"}')


#Replicas info 

@monitor_bp.route('/monitor/replicas_info/<string:namespace>',methods=['GET'])
def get_replicas(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='kube_replicaset_labels{namespace=~"'+namespace+'"}')

#get number of pods running each replica 
@monitor_bp.route('/monitor/replicas_pods/<string:namespace>',methods=['GET'])
def get_replica_pods(replicaset):
    return prometheus.query(metric='kube_replicaset_labels{replicaset=~"'+replicaset+'"}')

#pods table 
@monitor_bp.route('/monitor/pods_table/<string:namespace>',methods=['GET'])
def get_pods_info(pods):
    return prometheus.query(metric='kube_replicaset_labels{replicaset=~"'+pods+'"}')

# get persistent volumes
@monitor_bp.route('/monitor/persistent-volumes/info/<string:namespace>',methods=['GET'])
def get_persistent_volumes(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='kube_persistentvolume_info{kubernetes_namespace=~"'+namespace+'"}')


# get persistent volume claims
@monitor_bp.route('/monitor/persistent-volume-claims/info/<string:namespace>',methods=['GET'])
def get_persistent_volumes_claims(namespace):
    if (namespace == 'all'):
        namespace = '.*'
    return prometheus.query(metric='kube_persistentvolumeclaim_info{namespace=~"'+namespace+'"}')



#TODO get services, cluster status


