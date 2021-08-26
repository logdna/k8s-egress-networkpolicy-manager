# networkpolicy_manager

---

## Application Purpose

This is a `deployment` that runs within a cluster that needs to dynamically update an ingress CIDR mapping like a firewall, based on an external list of CIDRs like the ipcurator service. This system effectively can establish ip whitelisting capability reminiscent to a firewall.

## Quick Start Guide

### Kube Manifests

The (un-templated) k8s resources are found in `./src/networkpolicy_manager/deployments/minikube/manifest.yaml`

### Unit Tests

Run ` make test-pytest-networkpolicy_manager` in the root of the git directory

* NOTE: You will need pytest installed locally, if you do not have it `pip3 install pytest`

## Environment Variables 

This deployment accepts configuration from environment variables to modify certain aspects of behavior. The following
options are available:

| Variable Name(s) | Description | Default |
| ---|---|---|
|`LOGLEVEL`|Logging driver level can be DEBUG,INFO,WARN,ERROR |INFO|
|`LOGDATEFMT`|Date format used in logs|%Y-%m-%d %H:%M:%S|
|`LOGFORMAT`|Log format used in logs|%(asctime)s %(levelname)-8s %(message)s|
|`DEFAULT_REFRESH_RATE`|This is the interval (seconds) to refresh networkpolicies against external sources|60|
|`DEFAULT_POLICY_NAME_PREFIX`|The default rule name prefix to be used for networkpolicy objects|networkpolicy-manager-|
|`STRICT_CIDRS`|If this feature is enabled, all networkpolicy ingress CIDRs will be exact matches using /32 CIDR notation|false|

## Configuration Map (configmap)

This deployment requires a configmap object to define the endpoints you wish to collect internet IP CIDRs to whitelist your networkpolicy ingress from. An average configmap example, with description of options is offered below.

    ---
    kind: ConfigMap
    apiVersion: v1
    metadata:
      name: networkpolicy-manager-config
    data:
      ipcurator-sources.yaml: |
        ---
        - "http://ipcurator.servicie.somecluster.somehost.net:5000/v1/egress/namespace/default/pod/some_pod_egress":
            networkPolicy:
              auto_create_deny_all: False
              strict_cidrs: False
              namespace: default
              name_prefix: example-environment-
              ingress:
                podSelector: {"matchLabels": {"app": "some_pod_egress"}}
                ports:
                - protocol: TCP
                  port: 80
                - protocol: TCP
                  port: 443

