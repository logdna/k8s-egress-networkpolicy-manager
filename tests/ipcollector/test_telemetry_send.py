#!/usr/bin/env python3
import pytest
import requests
from ipcollector.tooling import send_payload
import json


i_expect_this_telemetry = {
    'ipaddr': {
        'external': '8.8.8.8',
        'host': '192.168.0.1'
    }
}


def test_payload():
    """
    see if payload function works using public utility
    """
    url = 'https://httpbin.org/post'
    payload = send_payload(i_expect_this_telemetry, url).json()['data']
    assert payload == json.dumps(i_expect_this_telemetry)