#!/usr/bin/env python3

from networkpolicy_manager import __version__
from networkpolicy_manager.config import App, load_config
from networkpolicy_manager.kubeapi import NetworkPolicyFacade
from networkpolicy_manager.policy import NetworkPolicy, Singleton
from networkpolicy_manager.policy import generate_networkpolicy_rules
from pprint import pprint
from retry import retry
from time import sleep
import logging
import requests

logging.basicConfig(format=App.config('LOGFORMAT'),
                    level=App.config('LOGLEVEL'),
                    datefmt=App.config('LOGDATEFMT'))

log = logging.getLogger(__name__)


@retry(Exception, delay=2, backoff=2, tries=3)
def get_cidrs_from_endpoints():
    """
    returns the cidr map from all the endpoints
    """
    endpoint_cidr_map = {}
    for i in App.config('CONFIGMAP_FROM_DISK'):
        for curator_endpoint, setting in i.items():
            log.info(f'* GET {curator_endpoint}')
            try:
                r = requests.get(curator_endpoint, timeout=15)
            except Exception as e:
                log.error(f'cannot get {curator_endpoint} due to exception: {e}')
                continue
            if r.status_code != 200:
                log.error(f'response code not 200 from {curator_endpoint}, skipping...')
                continue
            try:
                if setting['networkPolicy'].get('strict_cidrs') or App.config('STRICT_CIDRS'):
                    cidrs = [x+'/32' for x in r.json()['host_ips']]
                else:
                    cidrs = r.json()['host_cidrs']
                endpoint_cidr_map[curator_endpoint] = cidrs
            except ValueError as e:
                log.warn(f'remote response was: {r.text}')
                log.error(f'cannot decode {curator_endpoint} due to exception: {e}')
                continue
    log.debug(f'endpoint_cidr_map={endpoint_cidr_map}')
    return endpoint_cidr_map


def handle_api(rule, mode='create'):
    """
    handles the creation of both allow rule and deny rules with the kube api
    mode can be either 'createonce' or 'ensure' depending on desired behavior
    """
    if rule:
        rule_name = rule['metadata']['name']
        namespace = rule.get('metadata')['namespace']
        np = NetworkPolicyFacade(namespace)
        if np.exists(rule_name):
            if mode == 'ensure':
                log.info(f'replace rule={rule_name} namespace={namespace} method=kube-api mode={mode}')
                #np.replace(rule_name, rule)
                log.debug('delete rule')
                np.delete(rule_name)
                while(np.exists(rule_name)):
                    log.info('Sleeping 3s until networkpolicy deletes')
                    sleep(3)
                log.debug(f're-create rule with data: {rule}')
                np.create(rule)
            else:
                log.info(f'cannot create rule, already exists... rule={rule_name} namespace={namespace} method=kube-api mode={mode}')
        else:
            log.info(f'create rule={rule_name} namespace={namespace} method=kube-api')
            log.debug(f'allow_rule={rule}')
            np.create(rule)


def main():
    log.warn(f'{__name__.replace(".app", "")} version {__version__} starting up')
    context = Singleton.get_instance()
    while(True):
        log.debug('load CONFIGMAP from disk...')
        App.set('CONFIGMAP_FROM_DISK', load_config())
        log.info('poll remote host advertisement(s)...')
        cidr_map = get_cidrs_from_endpoints()
        ipcurator_endpoints = generate_networkpolicy_rules(cidr_map)
        log.debug(f'cidr map={cidr_map}')
        log.debug(f'remote_endpoints = {ipcurator_endpoints}')
        if context.data:
            cache = context.get()
        else:
            cache = {}
        for endpoint_url, networkpolicy in ipcurator_endpoints.items():
            # for each endpoint....
            log.debug(f'networkpolicy={networkpolicy}')
            if cache.get(endpoint_url):
                if cache[endpoint_url] == networkpolicy:
                    # check if the previously cached networkpolicy is what the projected networkpolicy is (check for change)
                    log.warn(f'SKIP networkpolicy updates because it is already up to date with remote endpoint {endpoint_url}')
                    continue
                else:
                    log.warn(f'networkpolicy requires an update from remote endpoint {endpoint_url}')
                    # log.warn(f'cache[endpoint_url]=={cache[endpoint_url]}')
                    # log.warn(f'networkpolicy=={networkpolicy}')
                    cache[endpoint_url] = networkpolicy
                    context.set(cache)
                    log.debug(f'cache={cache}')
            else:
                log.debug('endpoint_url not in cache yet, setting context...')
                cache[endpoint_url] = networkpolicy
                context.set(cache)
                log.debug(f'cache={cache}')
            # update behavior
            # ** create allow rule **
            allow_rule = networkpolicy['rules']['allow']
            handle_api(allow_rule, mode='ensure')
            # ** create deny rule **
            deny_rule = networkpolicy['rules']['deny']
            handle_api(deny_rule, mode='createonce')

        log.info(f'sleep for {App.config("DEFAULT_REFRESH_RATE")}s...')
        sleep(App.config('DEFAULT_REFRESH_RATE'))


if __name__ == "__main__":
    main()
