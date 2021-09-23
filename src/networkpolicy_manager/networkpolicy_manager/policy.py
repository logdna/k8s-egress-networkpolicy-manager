#!/usr/bin/env python3
from networkpolicy_manager.config import App
from slugify import slugify
import logging

log = logging.getLogger(__name__)


class NetworkPolicy:
    """
    self.object represents a valid k8s resource of ingress NetworkPolicy with some defalts,
    while any methods will help us construct a resource object in abstract
    """

    def __init__(self, name, namespace='default'):
        self.object = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'NetworkPolicy',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'spec': {
                'ingress': [],
                'policyTypes': [
                    'Ingress'
                ],
                'podSelector': {}
            }
        }

    def define_podselector(self, pod_selector):
        self.object['spec']['podSelector'] = pod_selector

    def define_ingress_policy(self, cidrs, ports):
        ingress = self.object['spec']['ingress']
        rule = {}
        result_cidrs = []
        for cidr in cidrs:
            result_cidrs.append({'ipBlock': {'cidr': cidr}})

        result_ports = []
        for port in ports:
            result_ports.append(port)

        rule['from'] = result_cidrs
        rule['ports'] = result_ports
        ingress.append(rule)


def generate_allow_rule(name, namespace, host_cidrs, ports, podselector):
    """
    generate cidr ingress networkpolicy for the pod selector
    """
    allow_rule = NetworkPolicy(name, namespace)
    allow_rule.define_ingress_policy(host_cidrs, ports)
    allow_rule.define_podselector(podselector)
    return allow_rule.object


def generate_deny_rule(name, namespace, podselector):
    """
    generate deny all ingress networkpolicy for the pod selector
    """
    deny_rule = NetworkPolicy(name, namespace)
    deny_rule.define_podselector(podselector)
    return deny_rule.object


def generate_networkpolicy_rules(cidr_map):
    """
    builds all the networkpolicy rules for each endpoint
    """
    endpoint_cidrs = {}
    for i in App.config('CONFIGMAP_FROM_DISK'):
        for curator_endpoint, setting in i.items():
            name_prefix = setting['networkPolicy'].get('name_prefix', '')
            if name_prefix == '':
                name_prefix = App.config('DEFAULT_POLICY_NAME_PREFIX')
            # config setting the namespace for a networkpolicy to exist within
            namespace = setting['networkPolicy'].get('namespace', 'default')
            # use slugify so a k8s safe name can be used
            name = f'{name_prefix}{slugify(curator_endpoint)}'
            if setting['networkPolicy'].get('name_override'):
                # config overload the name if desired
                name = setting['networkPolicy'].get('name_override')
                name = f'{name_prefix}{name}'

            # build ports if defined in config setting
            ports = setting['networkPolicy']['ingress'].get('ports', [])
            # build cidr whitelist based on the cidr map found on the external cluster
            try:
                host_cidrs = cidr_map[curator_endpoint]
            except KeyError:
                log.error(f'missing expected data for {curator_endpoint} it is possible the endpoint was down, skipping endpoint...')
                continue
            # build the podSelection strategy based on config setting
            podselector = setting['networkPolicy']['ingress'].get('podSelector', {})

            allow_rule = generate_allow_rule(name, namespace, host_cidrs, ports, podselector)
            if setting['networkPolicy'].get('auto_create_deny_all'):
                deny_rule = generate_deny_rule(f'deny-{name}', namespace, podselector)
            else:
                deny_rule = {}
            # rules to manage
            endpoint_cidrs[curator_endpoint] = {'rules': {'allow': allow_rule, 'deny': deny_rule}}
    return endpoint_cidrs


class Singleton:
    """
    singleton instance to store the network policy(s), we will track if they change between poll intervals
    """
    __instance = None

    def __init__(self):
        """
        private constructor
        """
        if Singleton.__instance is not None:
            raise Exception(
                "This class is a singleton, don't use parenthesis!")
        else:
            Singleton.__instance = self
            self.data = None

    @staticmethod
    def get_instance():
        """
        return singleton instance
        """
        if Singleton.__instance is None:
            Singleton()
        return Singleton.__instance

    def set(self, data):
        """
        set the current Singleton
        """
        self.data = data

    def get(self):
        """
        return the current Singleton
        """
        return self.data
