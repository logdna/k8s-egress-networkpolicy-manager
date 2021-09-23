# ipcurator

---

## Application Purpose

This is a `deployment` that runs as a REST endpoint as a resource to externally query the egress IP from specific nodes in the kubernetes cluster. This allows users or services to query over REST egress IPs for various nodes, such as:

* All nodes in a cluster
* All pods in a namespace
* All pods in a namespace with a partially matching pod name
* All pods in a namespace with a partially matching pod name. And a set of matching key/value labels or annotations.

This can be useful in purposes of exposing potential egress IPs to customers, vendors, partners, etc. You can further limit the egress IP range set by using pod nodeSelector in your applications, of course.

## Quick Start Guide

### Kube Manifests

The (un-templated) k8s resources are found in `./src/ipcurator/deployments/minikube/manifest.yaml`

### Unit Tests

Run ` make test-pytest-ipcurator` in the root of the git directory

* NOTE: You will need pytest installed locally, if you do not have it `pip3 install pytest`

## Environment Variables 

The agent accepts configuration from environment variables to modify certain aspects of behavior. The following
options are available:

| Variable Name(s) | Description | Default |
| ---|---|---|
|`CALCULATE_EFFICIENT_CIDRS`|If set to true then the output of host_cidrs will be calculated matching the smallest reasonable CIDR mask within a much larger ASN block. This is used to reduce load on firewall or ACL systems.|True|
|`LOGLEVEL`|Logging driver level can be DEBUG,INFO,WARN,ERROR |INFO|
|`ALLOWED_NAMESPACES`|This is a comma seperated list of namespaces that you want to grant this API access over querying pod external IP addresses.|*|
|`RESPONSE_NOTE`|Note key field to be displayed in response to IP addresses|none|
|`REVEAL_VERSION_ON_INDEX_PAGE`|When set to true, reveals the version of this application in the main route ('/')|true|

## API Endpoint Specifications

### / (root)

**Description**: Application banner message (JSON)

**URL** : `/`

**Method** : `GET`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

    {
            "app": "ipcurator",
            "tagline" : "You Know, For IP Egress Mappings"
    }

#### /v1/telemetry

**Description**: Receiving endpoint for public IP telemetry reports from ipcollector `daemonset`

**URL** : `/v1/telemetry`

**Method** : `POST`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

     OK

#### /v1/periodic/get_public_ip_address

**Description**: This route is triggered every minute by a sidecar. This allows for configurations where the /v1/nodes endpoint in kubernetes is aware of the external-ip for a cluster. This allows some clusters to not require use of the `daemonset` called `ipcollector`.

**URL** : `/v1/periodic/get_public_ip_address`

**Method** : `GET`

##### Success Responses

**Condition** : When public IP address was acquired from the kube-api

**Code** : `200 OK`

**Content** :

    {'status': 'ok', 'message': 'public ip addresses saved'}


##### Other Responses

**Condition** : When public IP data is unavailable from the kube-api. This means you will need to deploy the `daemonset` called `ipcollector` for this service to function.

**Code** : `400 BAD REQUEST`

**Content** :

    {'status': 'error', 'message': 'cannot determine node public ip using /v1/nodes k8s api, we suggest you deploy ipcollector daemonset in this cluster to get external ip addresses'}


#### /v1/periodic/getpods

**Description**: This route is triggered every minute by a sidecar. This keeps a fresh list of pod data in memory for clients to query the service.

**URL** : `/v1/periodic/getpods`

**Method** : `GET`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

     OK


#### /health

**Description**: Health endpoint

**URL** : `/health`

**Method** : `GET`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

     OK

### /v1/egress/all

**Description**: List all egress IPs within the cluster

**URL** : `/v1/egress/ns/(namespace)`

**Method** : `GET`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

NOTE: The output `host_cidrs` is calculated with the smallest applicable CIDR based on the highest and lowest specified k8s node IP inside the same netblock/ASN. This is significantly more secure then whitelisting an ASN, but it could include host blocks outside of your delegated control based on your cloud providers IPAM. If this happens to be a security issue, you can enable strict_cidrs which is documented in `docs/networkpolicy_manager.md` which will cause all CIDR notations to use `/32`.

    {"host_cidrs":["3.134.125.210/32"],"host_ips":["3.134.125.210"]}

### /v1/egress/ns/(namespace)

**Description**: List all egress IPs for pods existing in a specific namespace.

**URL** : `/v1/egress/ns/(namespace)`

**Method** : `GET`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

    {"host_cidrs":["3.134.125.210/32"],"host_ips":["3.134.125.210"]}

### /v1/egress/ns/(namespace)/pod/(podname partial)

**Description**: List all egress IPs for pods existing in a specific namespace, with a partially matching pod name. 

**URL** : `/v1/egress/ns/(namespace)/pod/(podname partial)`

**Method** : `GET`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

    {"host_cidrs":["3.134.125.210/32"],"host_ips":["3.134.125.210"]}

## /v1/egress/ns/(namespace)/pod/(podname partial)?label1=value1&label2=value2

**Description**: List all egress IPs for pods existing in a specific namespace, with a partially matching pod name. Adds optional requirement for two labels label1=value1 and label2=value2.

**URL** : `/v1/egress/ns/(namespace)/pod/(podname partial)?label1=value1&label2=value2`

**Method** : `GET`

##### Success Responses

**Condition** : Normal response

**Code** : `200 OK`

**Content** :

    {"host_cidrs":["3.134.125.210/32"],"host_ips":["3.134.125.210"]}



