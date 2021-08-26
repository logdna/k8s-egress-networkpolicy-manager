# k8s-egress-networkpolicy-manager

Kubernetes toolset allowing various external egress IP discovery methods and whitelisting of pod egress between clusters with NetworkPolicy

---

## Introduction

### What this solves

If you manage k8s in a variety of platform environments (such as Equinix, IBM, AWS and have been on Azure.) The problem is the way SNAT or Egress IP is managed is different on each and every platform (if supported at all.)

This project aims to support all environments cloud agnostically as a way to inform external clients the egress IP ranges for various pods in a kubernetes cluster. As a bonus, this project includes a networkpolicy-manager deployment that can connect to the ipcurator service to whitelist ingress from a neighboring cluster.

This tool solves for the issue of revisiting our network CNI choice for a simple matter of whitelisting services in neighboring clusters.

### Architecture Diagrams

![](images/overview.png)

![](images/ipcollector_ipcurator.png)

![](images/networkpolicymanager.png)


## Quick Start Guide

### Unit Tests

    make tests

### Run in minikube

This will start all the services in a single minikube cluster for testing or demo purposes.

    make minikube

