#!/usr/bin/env python3
import pytest
import requests
from ipcollector.ipaddr import GetIp, valid_ip, collect_ip, shorten_ip, valid_ip
from ipcollector.config import App

# control "truth" for tests
control_ipaddr = requests.get('https://icanhazip.com', timeout=5).text.strip()

class TestProvider():
    """
    test all of the ip source sites for a matching response against our control
    downtime is permitted (hence the source count)

    if 50% of these fail someday then the app can start taking a while to acquire a "lock"
    much like an old gps
    """
    def test_amazonaws_com(self):
        assert GetIp.amazonaws_com() == control_ipaddr

    def test_dyndns_org(self):
        assert GetIp.dyndns_org() == control_ipaddr

    def test_icanhazip_com(self):
        assert GetIp.icanhazip_com() == control_ipaddr

    def test_ident_me(self):
        assert GetIp.ident_me() == control_ipaddr

    def test_ipgrab_io(self):
        assert GetIp.ipgrab_io() == control_ipaddr

    def test_ifconfig_co(self):
        assert GetIp.ifconfig_co() == control_ipaddr

    def test_ifconfig_me(self):
        assert GetIp.ifconfig_me() == control_ipaddr

    def test_ipconfig_in(self):
        assert GetIp.ipconfig_in() == control_ipaddr

    def test_ipecho_net(self):
        assert GetIp.ipecho_net() == control_ipaddr

    def test_ipify_org(self):
        assert GetIp.ipify_org() == control_ipaddr

    def test_ipinfo_io(self):
        assert GetIp.ipinfo_io() == control_ipaddr

    # def test_myip_com(self):
    #     assert GetIp.myip_com() == control_ipaddr

    def test_seeip_org(self):
        assert GetIp.seeip_org() == control_ipaddr

    def test_whatismyipaddress_com(self):
        assert GetIp.whatismyipaddress_com() == control_ipaddr


def test_shorten_ip_positive():
    """
    see if the shorten ip works (128 character test)
    """
    long_ip = 'why curve officer kitchen range teeth teach creature everywhere why column shout numeral because held doubt fifth shoot very pretty mile bat crew receive'
    short_ip = 'why curve officer kitchen range teeth teach creature everywhere why column shout numeral because held doubt fifth shoot very pre'
    assert shorten_ip(long_ip) == short_ip
    assert shorten_ip('loremipsum') == 'loremipsum'


def test_valid_ipv4_positive():
    assert valid_ip('192.168.0.1') == '192.168.0.1'
    assert valid_ip('255.255.255.255') == '255.255.255.255'
    assert valid_ip('8.8.8.8') == '8.8.8.8'


def test_invalid_ipv4_negative():
    assert valid_ip('255.255.255.255.255.255.255.255') == None
    assert valid_ip('') == None


def test_valid_ipv6_positive():
    assert valid_ip('2001:0db8:85a3:0000:0000:8a2e:0370:7334') == '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
    assert valid_ip('2001:0db8:3c4d:0015:0000:0000:1a2f:1a2b') == '2001:0db8:3c4d:0015:0000:0000:1a2f:1a2b'
    assert valid_ip('2041:0000:140F:0000:0000:0000:875B:131B') == '2041:0000:140F:0000:0000:0000:875B:131B'
    assert valid_ip('2001:db8:3c4d:15::1a2f:1a2b') == '2001:db8:3c4d:15::1a2f:1a2b' # shorthand style
    assert valid_ip('2041:0000:140F::875B:131B') == '2041:0000:140F::875B:131B' # shorthand style
    assert valid_ip('2041:0:140F::875B:131B') == '2041:0:140F::875B:131B' # even shorter (of the above shorthand!)
    assert valid_ip('2001:0001:0002:0003:0004:0005:0006:0007') == '2001:0001:0002:0003:0004:0005:0006:0007'
    assert valid_ip('2001:1:2:3:4:5:6:7') == '2001:1:2:3:4:5:6:7' # shorthand of above
    assert valid_ip('2041:0000:140F:1234:1234:6543:875B:131B') == '2041:0000:140F:1234:1234:6543:875B:131B'
    assert valid_ip('2041:0:140F:1234:1234:6543:875B:131B') == '2041:0:140F:1234:1234:6543:875B:131B' # shorthand of above


def test_invalid_ipv6_negative():
    assert valid_ip('18:36:F3:98:4F:9A') == None
    assert valid_ip('684D:1111:222:3333:4444:5555:6:77 ') == None
    assert valid_ip('') == None


def test_main_function():
    """
    test the base function that retrieves an ip at a high level (does it all work now?)
    """
    assert collect_ip() == control_ipaddr
