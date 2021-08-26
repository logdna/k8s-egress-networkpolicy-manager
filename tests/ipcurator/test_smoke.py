#!/usr/bin/env python3
# stand up a mini environment on minikube to smoke test with
# you must have minikube installed for this to wor appropriately
import kubernetes
import pytest
import time
import subprocess
import requests
import json
from retry import retry

# pip3 install pytest kubernetes

NAMESPACE = 'default'
CURATOR_SERVICE_NAME = 'ipcurator-nodeport'


# in a larger example, this section could easily be in conftest.py
@pytest.fixture
def kube_v1_client():
    kubernetes.config.load_kube_config()
    v1 = kubernetes.client.CoreV1Api()
    return v1

@pytest.fixture(scope='module')
def kubectl_proxy():
    # establish proxy for kubectl communications
    # https://docs.python.org/3/library/subprocess.html#subprocess-replacements
    proxy = subprocess.Popen(
        'kubectl proxy --disable-filter=true --reject-methods="PUT,PATCH" &', stdout=subprocess.PIPE, shell=True)
    yield
    # terminate the proxy
    proxy.kill()

@pytest.mark.dependency()
def test_ensure_kubectl_context_is_minikube():
    process_result = subprocess.run(   [ 'kubectl', 'config', 'current-context'], text=True, check=True, capture_output=True).stdout
    assert process_result.strip() == 'minikube'

@pytest.mark.dependency(depends=['test_ensure_kubectl_context_is_minikube'])
def test_kubernetes_components_healthy(kube_v1_client):
    # iterates through the core kuberneters components to verify the cluster is reporting healthy
    ret = kube_v1_client.list_component_status()
    for item in ret.items:
        assert item.conditions[0].type == 'Healthy'
        print("%s: %s" % (item.metadata.name, item.conditions[0].type))


@pytest.mark.dependency(depends=['test_kubernetes_components_healthy'])
def test_deployment():
    # https://docs.python.org/3/library/subprocess.html#subprocess.run
    # using check=True will throw an exception if a non-zero exit code is returned, saving us the need to assert
    # using timeout=10 will throw an exception if the process doesn't return within 10 seconds
    # Enables the deployment
    #process_result = subprocess.run(
    #    'kubectl apply -f ../../../deployments/ipcurator/minikube', check=True, shell=True, timeout=10)
    process_result = subprocess.run(
        'kubectl apply -f deployments/ipcurator/minikube', check=True, shell=True, timeout=10)


@pytest.mark.dependency(depends=['test_deployment'])
def test_list_pods(kube_v1_client):
    ret = kube_v1_client.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print('%s\t%s\t%s' %
              (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


@pytest.mark.dependency(depends=['test_deployment'])
def test_deployment_ready(kube_v1_client):
    TOTAL_TIMEOUT_SECONDS = 300
    DELAY_BETWEEN_REQUESTS_SECONDS = 5
    REQUEST_TIMEOUT_SECONDS = 2
    apps_client = kubernetes.client.AppsV1Api()
    now = time.time()
    while (time.time() < now+TOTAL_TIMEOUT_SECONDS):
        api_response = apps_client.list_namespaced_deployment('default',
                                                              timeout_seconds=REQUEST_TIMEOUT_SECONDS)
        print('name\tavail\tready')
        for i in api_response.items:
            print("%s\t%s\t%s" %
                  (i.metadata.name, i.status.available_replicas, i.status.ready_replicas))
            if i.metadata.name == 'flask':
                if i.status and i.status.ready_replicas:
                    return
        time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)
    assert False


@pytest.mark.dependency(depends=['test_deployment_ready'])
def test_pods_running(kube_v1_client):
    TOTAL_TIMEOUT_SECONDS = 300
    DELAY_BETWEEN_REQUESTS_SECONDS = 5
    now = time.time()
    while (time.time() < now+TOTAL_TIMEOUT_SECONDS):
        pod_list = kube_v1_client.list_namespaced_pod('default')
        print('name\tphase\tcondition\tstatus')
        for pod in pod_list.items:
            for condition in pod.status.conditions:
                print("%s\t%s\t%s\t%s" % (pod.metadata.name,
                                          pod.status.phase, condition.type, condition.status))
                if condition.type == 'Ready' and condition.status == 'True':
                    return
        time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)
    assert False


@retry(Exception, delay=2, backoff=1, tries=8)
@pytest.mark.dependency(depends=['test_deployment_ready'])
def test_service_response_200(kube_v1_client, kubectl_proxy):
    """
    tests to ensure the service is ready for requests
    @retries a bit as the service takes a while to respond as not 503
    """
    uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy/' % (
        NAMESPACE, CURATOR_SERVICE_NAME)
    r = requests.get(uri)
    assert r.json().get('app') == 'ipcurator'
    assert r.json().get('tagline') == 'You Know, For IP Egress Mappings'
    assert r.status_code == 200

@pytest.mark.dependency(depends=['test_service_response_200'])
def test_health_endpoint(kube_v1_client, kubectl_proxy):
    uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
        NAMESPACE, CURATOR_SERVICE_NAME)
    uri = f'{uri}/health'
    r = requests.get(uri)
    assert r.text == 'OK'
    assert r.status_code == 200

@pytest.mark.dependency(depends=['test_service_response_200'])
def test_health_endpoint(kube_v1_client, kubectl_proxy):
    uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
        NAMESPACE, CURATOR_SERVICE_NAME)
    uri = f'{uri}/health'
    r = requests.get(uri)
    assert r.text == 'OK'
    assert r.status_code == 200

@pytest.mark.dependency(depends=['test_service_response_200'])
def test_getpods(kube_v1_client, kubectl_proxy):
    uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
        NAMESPACE, CURATOR_SERVICE_NAME)
    uri = f'{uri}/v1/periodic/getpods'
    r = requests.get(uri)
    assert r.text == 'OK'
    assert r.status_code == 200

@pytest.mark.dependency(depends=['test_service_response_200'])
def test_get_public_ip_address_error(kube_v1_client, kubectl_proxy):
    """
    this doesn't work by default in minikube so lets test the error it generates in such an environment
    """
    uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
        NAMESPACE, CURATOR_SERVICE_NAME)
    uri = f'{uri}/v1/periodic/get_public_ip_address'
    r = requests.get(uri)
    assert (r.status_code == 400) or (r.status_code == 201)

@pytest.mark.dependency(depends=['test_service_response_200'])
class TestTelemetryEgressEndpoints:
    """
    test for the /v1/telemetry and /v1/egress endpoints

    uploads some mock data, and then validates the api works
    """
    def test_upload_telemetry_endpoint(kube_v1_client, kubectl_proxy):
        """
        insert some test telemetry
        # curl -XPOST --data '{"ipaddr": {"external": "169.254.0.1", "host": "minikube"}}' http://localhost:8001/api/v1/namespaces/default/services/ipcurator-nodeport/proxy/v1/telemetry
        """
        uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
            NAMESPACE, CURATOR_SERVICE_NAME)
        uri = f'{uri}/v1/telemetry'
        telemetry = {
            'ipaddr': {
                'external': '169.254.0.1',
                'host': 'minikube'
            }
        }
        r = requests.post(uri, json=telemetry)
        assert r.text == 'OK'
        assert r.status_code == 200

    def test_egress_query_ns(kube_v1_client, kubectl_proxy):
        uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
            NAMESPACE, CURATOR_SERVICE_NAME)
        uri = f'{uri}/v1/egress/namespace/{NAMESPACE}'
        r = requests.get(uri)
        assert r.json() == {"host_cidrs":["169.254.0.1/32"],"host_ips":["169.254.0.1"]}
        assert r.status_code == 200

    def test_egress_query_ns_pod(kube_v1_client, kubectl_proxy):
        uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
            NAMESPACE, CURATOR_SERVICE_NAME)
        uri = f'{uri}/v1/egress/namespace/{NAMESPACE}/pod/ipcurator'
        r = requests.get(uri)
        assert r.json() == {"host_cidrs":["169.254.0.1/32"],"host_ips":["169.254.0.1"]}
        assert r.status_code == 200

    def test_egress_query_ns_pod_with_label(kube_v1_client, kubectl_proxy):
        uri = 'http://localhost:8001/api/v1/namespaces/%s/services/%s/proxy' % (
            NAMESPACE, CURATOR_SERVICE_NAME)
        uri = f'{uri}/v1/egress/namespace/{NAMESPACE}/pod/ipcurator?app.kubernetes.io/instance=k8s_egress_networkpolicy-ipcurator'
        r = requests.get(uri)
        assert r.json() == {"host_cidrs":["169.254.0.1/32"],"host_ips":["169.254.0.1"]}
        assert r.status_code == 200

