import os
import math
import re
from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_kube_config(context='context')

def convert_cpu(cpu): # Returns CPU in m 
    cpu, suffix = re.match(r'(\d+)([^\d]+)', cpu).groups()
    cpu = int(cpu)
    if suffix == 'n':
        cpu = cpu * (1e-6)
    elif suffix == 'm':
        pass
    else:
        raise ValueError("unsupported cpu suffix: %r" % suffix)
    return math.ceil(cpu)

def convert_mem(mem): # Returns Mem in Mi
    mem, suffix = re.match(r'(\d+)([^\d]+)', mem).groups()
    mem = int(mem)
    if suffix == 'Ki':
        mem = int(mem * 1e-3)
    elif suffix == 'Mi':
        pass
    elif suffix == 'Gi':
        mem = int(mem * 1e3)
    else:
        raise ValueError("unsupported memory suffix: %r" % suffix)
    return math.ceil(mem)

def get_pods_avg_mem_cpu(pod_metrics_list):
    total_pods = len(pod_metrics_list['items'])
    cpu = 0
    mem = 0
    for pod in pod_metrics_list['items']:
        if len( pod['containers']) == 2:
            cpu = cpu + convert_cpu(pod['containers'][0]['usage']['cpu']) + convert_cpu(pod['containers'][1]['usage']['cpu'])
            mem = mem + convert_mem(pod['containers'][0]['usage']['memory']) + convert_mem(pod['containers'][1]['usage']['memory'])
        else:
            cpu = cpu + convert_cpu(pod['containers'][0]['usage']['cpu'])
            mem = mem + convert_mem(pod['containers'][0]['usage']['memory'])
    cpu = cpu/total_pods
    mem = mem/total_pods
    return math.ceil(cpu), math.ceil(mem)

def get_app_resources(appname):
    api = client.CustomObjectsApi()
    label_selector = f"app={appname}"
    pod_metrics_list = api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "pods", label_selector=label_selector)
    cpu, mem = get_pods_avg_mem_cpu(pod_metrics_list)
    cpu = str(cpu) + 'm'
    mem = str(mem) + 'Mi'
    return cpu, mem
