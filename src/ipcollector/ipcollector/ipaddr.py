#!/usr/bin/env python3
from ipcollector.config import App
from retry import retry
from time import sleep
import logging
import random
import re
import requests

log = logging.getLogger(__name__)


def get_external_ip(ip_providers):
    """
    retrieve external internet ip
    """
    try:
        providers = random.sample(list(ip_providers), 2)  # select two random providers in a set
        try:
            ip0 = providers[0]()
        except:
            log.error('cannot contact first (ip0) provider in selected pair')
            ip0 = 'ERROR-0'  # this will never eval in match
        try:
            ip1 = providers[1]()
        except:
            log.error('cannot contact second (ip1) provider in selected pair')
            ip1 = 'ERROR-1'  # this will never eval in match
        if ip0 == ip1:
            log.info('ip address confirmed by two providers')
            return ip0
        else:
            log.warn('one of two providers did not agree on IP address, restarting pod...')
            exit(1)
    except Exception as e:
        log.error(f'exception while fetching ip, we will try again. exception was: {e}')
        sleep(3)


def collect_ip():
    """
    returns an internet ip address (without burdon of nat) which is collectively verified from two
    independent ip providers for accuracy of results (in the event of malfunction or malice from one.)

    this routine loops infinitely until two ip providers return the same response to make this agent
    resistent if a provider is a "poison pill", is broken, has downtime or goes defunct.
    """
    ip_providers = (
        GetIp.amazonaws_com, GetIp.seeip_org, GetIp.ifconfig_me,  # , GetIp.myip_com,
        GetIp.icanhazip_com, GetIp.ipgrab_io, GetIp.ipify_org, GetIp.ipinfo_io,
        GetIp.ipecho_net, GetIp.ipconfig_in, GetIp.ifconfig_co, GetIp.dyndns_org,
        GetIp.ident_me, GetIp.whatismyipaddress_com)
    while True:
        # keep trying until IP lock is acquired
        if App.config('IP_TRUTH_SOURCE') == 'internet-ip':
            return get_external_ip(ip_providers)
        else:
            log.error(f'error - this pod shouldnt be running because of IP_TRUTH_SOURCE=node-external-ip')
            sleep(30)
            exit(1)


def shorten_ip(ipaddr):
    """
    only returns first 128 characters of "ip" response which could be html if the page is flaking out
    """
    return ipaddr[:min(len(ipaddr), 128)]


def valid_ip(ipaddr):
    """
    takes a string representation of ip address and ensures it validates
    if valid, returns the address
    if invalid, returns None
    """
    ipv4_re = r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
    ipv6_re = r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$'
    if re.match(ipv4_re, ipaddr) or re.match(ipv6_re, ipaddr):
        return ipaddr
    else:
        log.error(f'error - the ip address received does not seem valid, this was given: {shorten_ip(ipaddr)}')
        return None


class GetIp():
    """
    contains the static methods used to get public IPaddr from various providers
    leaving various methods a bit loose to keep things easy to change and adapt
    """

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def amazonaws_com():
        url = 'https://checkip.amazonaws.com'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text.strip()
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    # @staticmethod
    # @retry(Exception, delay=2, backoff=0, tries=3)
    # def myip_com():
    #     url = 'https://api.myip.com'
    #     log.info(f'get ip from {url}')
    #     ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).json()['ip']
    #     log.info(f'{url} says {shorten_ip(ip)}')
    #     return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def seeip_org():
        url = 'https://ip.seeip.org/'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ifconfig_me():
        url = 'https://ifconfig.me'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def icanhazip_com():
        url = 'https://icanhazip.com'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text.strip()
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ipgrab_io():
        url = 'https://ipgrab.io'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text.strip()
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ipify_org():
        url = 'https://api.ipify.org?format=json'
        log.info(f'get ip from {url}')
        r = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).json()
        ip = r['ip']
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ipinfo_io():
        url = 'https://ipinfo.io/ip'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ipecho_net():
        url = 'http://ipecho.net/plain'
        log.info(f'get ip from {url}')
        ip = requests.get(url, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ipconfig_in():
        url = 'http://ipconfig.in/ip'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text.strip()
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ifconfig_co():
        url = 'http://ifconfig.co'
        headers = {'User-Agent': 'curl/7.64.1'}
        log.info(f'get ip from {url}')
        ip = requests.get(url, headers=headers, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text.strip()
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def dyndns_org():
        url = 'http://checkip.dyndns.org'
        log.info(f'get ip from {url}')
        r = requests.get(url, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text
        ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', r)[0]
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def ident_me():
        url = 'https://ident.me'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))

    @staticmethod
    @retry(Exception, delay=2, backoff=0, tries=3)
    def whatismyipaddress_com():
        url = 'https://bot.whatismyipaddress.com'
        log.info(f'get ip from {url}')
        ip = requests.get(url, verify=False, timeout=App.config('DEFAULT_REQUEST_TIMEOUT')).text
        log.info(f'{url} says {shorten_ip(ip)}')
        return(valid_ip(ip))
