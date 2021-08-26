

from networkpolicy_manager.policy import generate_networkpolicy_rules, generate_allow_rule, generate_deny_rule

def test_allow_policy_object_generator():
    test_expect = {'apiVersion': 'networking.k8s.io/v1', 'kind': 'NetworkPolicy', 'metadata': {'name': 'test', 'namespace': 'testns'}, 'spec': {'ingress': [{'from': [{'ipBlock': {'cidr': '192.168.0.1/32'}}], 'ports': []}], 'policyTypes': ['Ingress'], 'podSelector': {}}}
    assert generate_allow_rule('test', 'testns', ['192.168.0.1/32'], [], {}) == test_expect

def test_deny_policy_object_generator():
    test_expect = {'apiVersion': 'networking.k8s.io/v1', 'kind': 'NetworkPolicy', 'metadata': {'name': 'test', 'namespace': 'testns'}, 'spec': {'ingress': [], 'policyTypes': ['Ingress'], 'podSelector': {}}}
    assert generate_deny_rule('test', 'testns', {}) == test_expect

def test_networkpolicy_rule_object_generator():
    cidr_map = {'http://ipcurator:5000/v1/egress/namespace/default/pod/ipcurator': ['169.254.114.107/32']}

    test_expect = {
   "http://ipcurator:5000/v1/egress/namespace/default/pod/ipcurator": {
      "rules": {
         "allow": {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
               "name": "example-environment-http-ipcurator-5000-v1-egress-namespace-default-pod-ipcurator",
               "namespace": "default"
            },
            "spec": {
               "ingress": [
                  {
                     "from": [
                        {
                           "ipBlock": {
                              "cidr": "169.254.114.107/32"
                           }
                        }
                     ],
                     "ports": [
                        {
                           "port": 80,
                           "protocol": "TCP"
                        }
                     ]
                  }
               ],
               "podSelector": {
                  "matchLabels": {
                     "app": "ipcurator"
                  }
               },
               "policyTypes": [
                  "Ingress"
               ]
            }
         },
         "deny": {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
               "name": "deny-example-environment-http-ipcurator-5000-v1-egress-namespace-default-pod-ipcurator",
               "namespace": "default"
            },
            "spec": {
               "ingress": [],
               "podSelector": {
                  "matchLabels": {
                     "app": "ipcurator"
                  }
               },
               "policyTypes": [
                  "Ingress"
               ]
            }
         }
      }
   }
}
    assert generate_networkpolicy_rules(cidr_map) == test_expect