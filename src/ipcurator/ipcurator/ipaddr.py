#!/usr/bin/env python3
from ipcurator.singleton import AsnCache
from ipwhois import IPWhois
import logging
import netaddr

log = logging.getLogger(__name__)


def ip_is_in_mappings(ipaddr):
    context = AsnCache.get_instance()
    if context.data:
        cidrmappings = context.get()
    else:
        cidrmappings = {}
    for asn_cidr, ips in cidrmappings.items():
        for ip in ips:
            if ipaddr == ip:
                log.info(f'{ipaddr} found in mappings')
                return True
    log.info(f'{ipaddr} not found in mappings')
    return False


def sort_ipaddr_by_largest_cidr(ipaddrs):
    """
    checks ip whois for each ip address (list) and returns a dict
    where the key names is the largest possible cidr for a list of ipaddresses
    this is used because if the netaddr netblock span is too large it will calculcate cidrs like 0.0.0.0/4
    so therefore the output of this function sorts the batches we perform math upon
    """
    context = AsnCache.get_instance()
    for i in ipaddrs:
        if context.data:
            cidrmappings = context.get()
        else:
            cidrmappings = {}
        # build asn cidr to ip address mapping
        if not ip_is_in_mappings(i):
            obj = IPWhois(i)
            w = obj.lookup_whois()
            if cidrmappings.get(w['asn_cidr']):
                cidrmappings[w['asn_cidr']].append(i)
                context.set(cidrmappings)
            else:
                cidrmappings[w['asn_cidr']] = [i]
                context.set(cidrmappings)
    return cidrmappings


def find_smallest_common_cidr(ipaddrs):
    """
    prints a bunch of lines demonstrating the strictest cidr you can use to firewall ingress when given a list of large ip addresses
    """
    cidrs = {}
    asngroup = sort_ipaddr_by_largest_cidr(ipaddrs)
    for cidr, v in asngroup.items():
        if len(v) == 1:
            # if a node address exists by itself within an asn then we suggest a /32 cidr notation
            smallest = f'{v[0]}/32'
            cidrs[v[0]] = smallest
        else:
            smallest = netaddr.spanning_cidr(v)
            for i in v:
                cidrs[i] = str(smallest)
    return cidrs
