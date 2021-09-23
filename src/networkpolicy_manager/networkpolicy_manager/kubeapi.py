#!/usr/bin/env python3
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from retry import retry


class NetworkPolicyFacade:
    """
    facade to the interface of NetworkingV1Api for managing networkpolicy
    """

    def __init__(self, namespace='default'):
        try:
            config.load_incluster_config()
            self.api = client.NetworkingV1Api()
        except ApiException as e:
            raise ApiException(f'exception when calling NetworkingV1Api instanciation: {e}\n')
        self.namespace = namespace

    @retry(Exception, delay=2, backoff=2, tries=3)
    def set_namespaace(self, ns):
        """
        change namespace
        """
        self.namespace = ns

    @retry(Exception, delay=2, backoff=2, tries=3)
    def create(self, rule):
        """
        create
        """
        pretty = 'false'  # str | If 'true', then the output is pretty printed. (optional)
        field_manager = 'networkpolicy_manager'
        try:
            return self.api.create_namespaced_network_policy(self.namespace, rule, pretty=pretty, field_manager=field_manager)
        except ApiException as e:
            raise ApiException(f'exception when calling NetworkingV1Api->create_namespaced_network_policy: {e}\n')

    @retry(Exception, delay=2, backoff=2, tries=3)
    def replace(self, name, rule):
        """
        replace / update
        """
        pretty = 'false'  # str | If 'true', then the output is pretty printed. (optional)
        field_manager = 'networkpolicy_manager'
        try:
            return self.api.replace_namespaced_network_policy(name, self.namespace, rule, pretty=pretty, field_manager=field_manager)
        except ApiException as e:
            raise ApiException(f'exception when calling NetworkingV1Api->replace_namespaced_network_policy: {e}\n')

    @retry(Exception, delay=2, backoff=2, tries=3)
    def exists(self, name):
        """
        return bool if exists or not
        """
        try:
            networkpolicies = self.api.list_namespaced_network_policy(self.namespace).items
        except ApiException as e:
            raise ApiException(f'exception when calling NetworkingV1Api->list_namespaced_network_policy: {e}\n')

        for i in networkpolicies:
            if name == i.metadata.name:
                return True
        return False

    @retry(Exception, delay=2, backoff=2, tries=3)
    def delete(self, name):
        """
        delete a networkpolicy in a specific namespace
        """
        config.load_incluster_config()
        api = client.NetworkingV1Api()
        grace_period_seconds = 56
        pretty = 'true'  # str | If 'true', then the output is pretty printed. (optional)grace_period_seconds = 56 # int | The duration in seconds before the object should be deleted. Value must be non-negative integer. The value zero indicates delete immediately. If this value is nil, the default grace period for the specified type will be used. Defaults to a per object value if not specified. zero means delete immediately. (optional)
        propagation_policy = 'OrphanDependents'  # str | Whether and how garbage collection will be performed. Either this field or OrphanDependents may be set, but not both. The default policy is decided by the existing finalizer set in the metadata.finalizers and the resource-specific default policy. Acceptable values are: 'Orphan' - orphan the dependents; 'Background' - allow the garbage collector to delete the dependents in the background; 'Foreground' - a cascading policy that deletes all dependents in the foreground. (optional)
        body = client.V1DeleteOptions()  # V1DeleteOptions |  (optional)

        try:
            return self.api.delete_namespaced_network_policy(name, self.namespace, pretty=pretty, grace_period_seconds=grace_period_seconds, propagation_policy=propagation_policy, body=body)
        except ApiException as e:
            raise ApiException(f'exception when calling NetworkingV1Api->delete_namespaced_network_policy: {e}\n')

    @retry(Exception, delay=2, backoff=2, tries=3)
    def list(self):
        policies = self.api.list_namespaced_network_policy(self.namespace).items
        return policies
