#!/usr/bin/env python3
# pip3 install requests kubernetes retry
#                   ..       ,
#    *._  ___  _. _ || _  _.-+- _ ._.
#    |[_)     (_.(_)||(/,(_. | (_)[
#     |
#
# This agent runs on every k8s node collecting the current (internet) IP of each node.
# This data is forwarded to a service called ip-curator so users can find the egress
# IPs for certain pods.
#
# This pod should successfully function as long as 2 of the 12 ip providers are online.
# Albeit with very much degraded performance in such cases. Errors are logged liberally for troubleshooting.
#

from ipcollector import __version__
from ipcollector.config import App
from ipcollector.ipaddr import collect_ip
from ipcollector.tooling import send_payload, v1_list_pods, get_daemonset_node_name
from json import dumps
from kubernetes import config
from time import sleep
import logging
import os
import random
import re

logging.basicConfig(format=App.config('LOGFORMAT'),
                    level=App.config('LOGLEVEL'),
                    datefmt=App.config('LOGDATEFMT'))

log = logging.getLogger(__name__)


def main():
    log.warn(f'{__name__.replace(".app", "")} version {__version__} starting up')
    sleep(App.config('STARTUP_DELAY'))
    log.info('trying to acquire external ip address...')
    ip = collect_ip()
    log.info('loading in-cluster kube config')
    try:
        config.load_incluster_config()
    except Exception as e:
        log.error(f'error - exit code=1 - cannot load in-cluster config because of exception: {e}')
        exit(1)

    log.warning('acquiring k8s hostname for this pod from local kube-api...')
    try:
        pod_list = v1_list_pods().items
    except Exception as e:
        log.error(f'error - exit code=1 - cannot get pods in k8s api because of too many repeat exceptions: {e}')
        exit(1)
    daemonset_hostname = get_daemonset_node_name(pod_list)
    url = f'{App.config("CURATOR_PROTO")}://{App.config("CURATOR_HOSTNAME")}:{App.config("CURATOR_PORT")}{App.config("CURATOR_PATH")}?node={daemonset_hostname}'
    while True:
        telemetry = {
            'ipaddr': {
                'external': ip,
                'host': daemonset_hostname
            }
        }
        telem = dumps(telemetry)
        log.info(f'transmit payload {telem} to url {url}')
        if not ip:
            log.error('error - exit code=2 - ip was null')
            exit(2)
        try:
            send_payload(telemetry, url)
        except Exception as e:
            log.error(f'error - exit code=1 - cannot transmit payload to ipcurator at {url} because of too many repeat exceptions: {e}')
            exit(1)

        # sleep a random interval between updates
        sleeptime = random.uniform(App.config('TRANSMIT_MIN_INTERVAL_DELAY'), App.config('TRANSMIT_MAX_INTERVAL_DELAY'))
        log.info(f'transmit OK, sleeping {sleeptime} seconds')
        sleep(sleeptime)


if __name__ == "__main__":
    main()
