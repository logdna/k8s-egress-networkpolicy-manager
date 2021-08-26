#!/usr/bin/env python3
from kubernetes import client
from retry import retry
import logging
import requests
import socket

log = logging.getLogger(__name__)


@retry(Exception, delay=2, backoff=2, tries=15)
def send_payload(payload, url):
    """
    send payload telemetry json to the curator service
    """
    r = requests.post(url, json=payload)
    if r.status_code != 200:
        logging.warn(f'send payload error, status code not 200')
        raise()
    return r


@retry(Exception, delay=2, backoff=2, tries=15)
def v1_list_pods():
    """
    get a list of pod data from this cluster
    """
    v1 = client.CoreV1Api()
    v1_list_pods = v1.list_pod_for_all_namespaces(watch=False)
    return v1_list_pods


def get_daemonset_node_name(v1_pods):
    """
    return the host ip of the k8s node this pod is running on
    # from https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodStatus.md
    """
    for i in v1_pods:
        if i.metadata.name == socket.gethostname():
            return i.spec.node_name
