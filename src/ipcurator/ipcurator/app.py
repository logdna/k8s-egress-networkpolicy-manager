#!/usr/bin/env python3
#
#    |                        |
#    ||~~\---/~~|   ||/~\/~~|~|~/~\|/~\
#    ||__/   \__ \_/||   \__| | \_/|
#     |
#
# This webserver runs as a service in your cluster allowing clients to query the external CIDR IP (internet)
# that a given node is going to egress from. Various REST-style queries allow you to limit your request to a subset
# pods.
#

from IPy import IP
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask_httpauth import HTTPBasicAuth
from ipcurator import __version__
from ipcurator import __version__
from ipcurator.config import App
from ipcurator.ipaddr import find_smallest_common_cidr
from ipcurator.singleton import SourceIpTelemetry, Podlist, SmallCidrMap, SmallCidrLastUpdate
from kubernetes import client, config
from retry import retry
from time import time
import json
import json
import logging
import os
import re
import time

app = Flask(__name__, static_url_path="")
auth = HTTPBasicAuth()

logging.basicConfig(format=App.config('LOGFORMAT'),
                    level=App.config('LOGLEVEL'),
                    datefmt=App.config('LOGDATEFMT'))
log = logging.getLogger(__name__)


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'unauthorized access'}), 403)
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'not found'}), 404)


def build_pod_list(v1_pods):
    """
    return a list of pods from this cluster that also live on this pods k8s node
    """
    log.debug(f'build_pod_list')
    payload = []
    for i in v1_pods:
        payload.append({'node_name': i.spec.node_name, 'hostip': i.status.host_ip, 'pod': i.metadata.name, 'namespace': i.metadata.namespace,
                        'labels': i.metadata.labels, 'annotations': i.metadata.annotations})
    return payload


@retry(Exception, delay=2, backoff=2, tries=5)
def v1_list_pods():
    """
    gets a list of pod data (all namespaces) from this cluster
    """
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    log.debug(f'v1_list_pods')
    v1_list_pods = v1.list_pod_for_all_namespaces(watch=False)
    return v1_list_pods


@app.route('/v1/telemetry', methods=['POST'])
def store_sourceip_telemetry():
    """
    route to handle inbound telemetry from daemonset ip collector agents
    """
    # load up some context so we can append to it
    context = SourceIpTelemetry.get_instance()
    if context.data:
        telemetry = context.get()
    else:
        telemetry = {}
    payload = request.get_json(force=True)
    log.debug(f'request_data = {payload}')
    # setup dict key of hostip with value of external ip
    hostname = payload['ipaddr']['host']
    ipaddr = payload['ipaddr']['external']
    if not (hostname and ipaddr):
        log.error('ipaddr.host or ipaddr.external does not contain a valid value')
        return make_response(jsonify({'error': 'ipaddr.host or ipaddr.external seems to be missing in payload'}), 400)
    if not telemetry.get(hostname):
        log.info(f'new host saved in memory host={hostname} ipaddr={ipaddr}')
    telemetry[hostname] = ipaddr
    log.debug(f'context.set telemetry={telemetry}')
    context.set(telemetry)
    return 'OK'


@app.route('/v1/egress/all', methods=['GET'])
@app.route('/v1/egress/ns/<namespace>', methods=['GET'])
@app.route('/v1/egress/namespace/<namespace>', methods=['GET'])
@app.route('/v1/egress/ns/<namespace>/pod/<podname>', methods=['GET'])
@app.route('/v1/egress/namespace/<namespace>/pod/<podname>', methods=['GET'])
def show_pod_egress(namespace=None, podname=None):
    """
    route to query the IP assignments of specific functional
    namespaces or pods with optional labels as http query params
    consider this the "frontend" view of the app
    example: curl http://127.0.0.1:5000/v1/ns/default/pod/eeihehio?key1=value1&key2=value2 | jq 'with_entries(.cidrs = .cidrs) | del(.pods)'
    curl http://127.0.0.1:5000/v1/ns/default/pod/toolsz?key1=value1&key2=value2 | jq 'with_entries(.cidrs = .cidrs) | del(.pods) | .host_cidrs' -c
    echo "{\"tools\": $(curl http://127.0.0.1:5000/v1/ns/default/pod/toolsz?key1=value1&key2=value2 | jq 'with_entries(.cidrs = .cidrs) | del(.pods) | .host_cidrs' -c)}" | jq
    """
    # query param node allows you to toggle the query parameter search mode between handling pod labels or annotations
    query_param_mode = request.headers.get('x-query-param-mode', 'labels')
    if not query_param_mode in ['labels', 'annotations']:
        message = f'http header x-query-param-mode must be value of `labels\' or `annotations\', and not `{query_param_mode}\''
        return jsonify({"error": message}), 400
    # optional required labels on pod to filter response scope
    required_labels = request.args
    response = {
        'host_cidrs': [],
        'host_ips': [],
    }
    if App.config('RESPONSE_NOTE'):
        response['notice'] = App.config('RESPONSE_NOTE')
    hostips = []
    hostcidrs = []
    pods_context = Podlist.get_instance()
    query_param_bits = []
    # dictionary singleton of internal ips with external egress IP as value
    try:
        cidrcontext = SmallCidrMap.get_instance()
        if cidrcontext.data:
            smallcidr = cidrcontext.get()
        else:
            smallcidr = {}
        context = SourceIpTelemetry.get_instance()
        if context.data:
            telemetry = context.get()
        else:
            telemetry = {}
        if len(telemetry) == 0:
            return response
    except OSError as e:
        log.error(
            'error - exit code=1 - oserror while trying to get source telemetry')
        exit(1)
    try:
        pods = pods_context.get()
    except OSError as e:
        log.error('error - exit code=1 - oserror while trying to get pods context')
        exit(1)
    if pods:
        for pod in pods:
            pod_name = pod['pod']
            node_name = pod['node_name']
            if not node_name:
                log.debug('nodes are pending and excluded')
                continue
            if (not pod['namespace'] in App.config('ALLOWED_NAMESPACES')) and (App.config('ALLOWED_NAMESPACES') != ['*']):
                log.debug('not in allowed namespace')
                continue
            try:
                nodeip = telemetry[node_name]
                cidr = smallcidr.get(telemetry[node_name], telemetry[node_name] + '/32')
            except KeyError:
                log.debug(f'skip {node_name} from egress generated output because the egress appears to be missing (is a daemonset running on this host?)')
                continue
            if pod['namespace'] == namespace and not podname:
                log.debug(f'* {pod_name} found by namespace')
                hostips.append(nodeip)
                hostcidrs.append(cidr)
            elif pod['namespace'] == namespace and podname:
                if re.search(f'^{podname}*', pod_name) and not required_labels:
                    log.debug(f'* {pod_name} found by podname')
                    hostips.append(nodeip)
                    hostcidrs.append(cidr)
                elif re.search(f'^{podname}*', pod_name) and required_labels:
                    for k, v in required_labels.items():
                        if pod[query_param_mode].get(k) == v:
                            query_param_bits.append(True)
                        else:
                            query_param_bits.append(False)
                    if False not in query_param_bits:
                        log.debug(
                            f'* {pod_name} found by query parameter ({query_param_mode})')
                        hostips.append(nodeip)
                        hostcidrs.append(cidr)
            elif not namespace and not podname:
                log.debug(f'* {pod_name} found because its one of (all) pods requested')
                hostips.append(nodeip)
                hostcidrs.append(cidr)
    else:
        return(jsonify(response))
    # ~~ wrap up response ~~
    # remove duplicates addresses from hostip list
    hostips = list(dict.fromkeys(hostips))
    # appends /32 network cidr mask
    response['host_cidrs'] = list(set(hostcidrs))
    response['host_ips'] = list(set(hostips))
    return(jsonify(response))


@app.route('/v1/periodic/get_public_ip_address', methods=['GET'])
def get_public_ip_address():
    """
    triggered by a sidecar, every minute
    stores the public IP address if the /v1/nodes listing in kube api exposes public
    addresses for your kube nodes, if not you will need the ipcollector daemonset
    """
    context = SourceIpTelemetry.get_instance()
    if context.data:
        telemetry = context.get()
    else:
        telemetry = {}

    config.load_incluster_config()
    v1 = client.CoreV1Api()
    v1_k8s_node = v1.list_node(watch=False)

    for i in v1_k8s_node.items:
        external_ip = None
        hostname = None
        for i in i.status.addresses:
            # see https://kubernetes.io/docs/concepts/architecture/nodes/#addresses
            if i.type == 'ExternalIP':
                if IP(i.address).iptype() == 'PUBLIC':
                    external_ip = i.address
            if i.type == 'Hostname':
                hostname = i.address

        if not external_ip:
            log.debug(
                '`externalip\' is not found in kube-api /v1/nodes output, ipcollector daemonset is required')
        if not hostname:
            log.debug(
                '`hostname\' is not found in kube-api /v1/nodes output, ipcollector daemonset is required')
        if external_ip and hostname:
            # setup dict key of hostip with value of external ip
            telemetry[hostname] = external_ip
            context.set(telemetry)
    log.debug(f'/v1/get_public_ipaddress telem = {telemetry}')
    if len(telemetry) > 0:
        result = 'OK'
        return result, 201
    else:
        log.warning(f'this cluster requires input from ipcollector DaemonSet to build a public IP node mapping (/v1/nodes does not reveal public ip addresses)')
        return make_response(jsonify({'status': 'error', 'message': 'cannot determine node public ip using /v1/nodes k8s api, we suggest you deploy ipcollector daemonset in this cluster to get external ip addresses'}), 400)


@app.route('/v1/periodic/calculate_efficient_cidrs', methods=['GET'])
def determine_cidrs():
    """
    determine the limited subset of cidrs on a periodic schedule
    this process should not break the overall system if unreliable
    but rather simply enhance the rulesets already existing in the database
    """
    now = time()
    lastupdate = SmallCidrLastUpdate.get_instance()
    if lastupdate.data:
        lastupdated = lastupdate.get()
    else:
        lastupdated = now
    time_since = (now - lastupdated)
    if time_since > App.config('UPDATE_EFFICIENT_CIDR_INTERVAL'):
        log.info(f'time_since={time_since} lastupdated={lastupdated} now={now}')
        return (jsonify({'note': 'updates not scheduled to run yet', 'out': None}), 200)
    if not App.config('CALCULATE_EFFICIENT_CIDRS'):
        log.warning('CALCULATE_EFFICIENT_CIDRS config not set to true, efficient cidrs will not be calculated')
        return 204
    try:
        cidrcontext = SmallCidrMap.get_instance()
        if cidrcontext.data:
            smallcidr = cidrcontext.get()
        else:
            smallcidr = {}
        context = SourceIpTelemetry.get_instance()
        if context.data:
            telemetry = context.get()
        else:
            telemetry = {}
        if len(telemetry) == 0:
            return (jsonify({'note': 'no ipcollector telemetry was reported to operate on, please try again later', 'out': None}), 200)
    except OSError as e:
        log.error(
            'error - exit code=1 - oserror while trying to get source telemetry')
        exit(1)
    ipaddrs = []
    for hostname, ipaddr in telemetry.items():
        ipaddrs.append(ipaddr)
    shortened_cidrs = find_smallest_common_cidr(ipaddrs)
    cidrcontext.set(shortened_cidrs)
    lastupdate.set(now)
    return jsonify({'note': 'efficient cidrs calculated', 'out': shortened_cidrs}), 200


@app.route('/v1/periodic/getpods', methods=['GET'])
def periodic_getpods():
    """
    triggered by a sidecar, every 5 minutes
    uses v1api in kubernetes to keep the node singleton context updated with pods data, this
    should be run at least every 5 minutes
    """
    context = Podlist.get_instance()
    log.warning('save pod list from kube-api...')
    try:
        v1 = v1_list_pods().items
        pod_list = build_pod_list(v1)
    except Exception as e:
        log.info(
            f'error - updating pods in subprocess with k8s api encountered an exception in kubernetes: {e}')
        # exit will eventually cause CrashLoopBackOff in k8s if this keeps happening
        exit(1)
    log.debug(f'podlist={pod_list}')
    context.set(pod_list)
    return 'OK'


@app.route('/health', methods=['GET'])
def health():
    return 'OK'


@app.route('/version', methods=['GET'])
def version():
    return __version__


@app.route('/', methods=['GET'])
def index():
    response = {
        'app': 'ipcurator',
        'tagline': 'You Know, For IP Egress Mappings'
    }
    if App.config('REVEAL_VERSION_ON_INDEX_PAGE'):
        response['version'] = __version__
    return response


def main():
    log.warn(f'{__name__.replace(".app", "")} version {__version__} starting up')
    app.run(host="0.0.0.0", debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
