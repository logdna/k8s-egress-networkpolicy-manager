# ipcollector

---

## Application Design Description

This is a `daemonset` agent that runs on every node in a cluster and collects the IP address of each node using several external IP providers. Once an IP is determined, it is verified by a second provider. It is forwarded over HTTP to `ipcurator` API to be stored for queries by interested clients. This runs in an infinite loop with a random sleep interval.

If two providers don't match or there is issues acquiring an IP after a number of tries, the pod will restart in the hopes that a new pod network may resolve the issue.

### Supported IP Providers

The following external IP providers are supported:

* http://checkip.dyndns.org
* http://ifconfig.co
* http://ipconfig.in/ip
* http://ipecho.net
* https://api.myip.com
* https://checkip.amazonaws.com
* https://icanhazip.com
* https://ident.me
* https://ifconfig.me
* https://ipgrab.io
* https://ipify.org
* https://ipinfo.io
* https://ip.seeip.org
* https://whatismyipaddress.com

## Quick Start Guide

### Kube Manifests

The (un-templated) k8s resources are found in `./src/ipcollector/deployments/minikube/manifest.yaml`

### Unit Tests

Run ` make test-pytest-ipcollector` in the root of the git directory

* NOTE: You will need pytest installed locally, if you do not have it `pip3 install pytest`

## Environment Variables 

The agent accepts configuration from environment variables to modify certain aspects of behavior. The following
options are available:

| Variable Name(s) | Description | Default |
| ---|---|---|
|`LOGLEVEL`|Logging driver level can be DEBUG,INFO,WARN,ERROR |INFO|
|`CURATOR_PROTO`|Curator host protocol|http|
|`CURATOR_HOSTNAME`|Curator service hostname|ipcurator|
|`CURATOR_PORT`|Curator service port|5000|
|`CURATOR_PATH`|Request path for POSTing telemetry|/v1/telemetry|
|`STARTUP_DELAY`|Time (seconds) to wait before the agent attempts to do anything|0|
|`TRANSMIT_MIN_INTERVAL_DELAY`|Minimum interval sleep delay between transmitting telemetry to ipcurator|60|
|`TRANSMIT_MAX_INTERVAL_DELAY`|Maximum interval sleep delay between transmitting telemetry to ipcurator|180|
|`DEFAULT_REQUEST_TIMEOUT`|Time (seconds) for http request(s) to timeout|5|
