#!/usr/bin/env python3
from os import environ


class App:
    """
    simple config storage class, allows to set and get
    it has a whitelist for setters!
    """
    __conf = {
        'LOGLEVEL': environ.get('LOGLEVEL', 'INFO'),
        'LOGDATEFMT': environ.get('LOGDATEFMT', '%Y-%m-%d %H:%M:%S'),
        'LOGFORMAT': environ.get('LOGFORMAT', '%(asctime)s %(levelname)-8s %(message)s'),
        # or internet-ip
        'IP_TRUTH_SOURCE': environ.get('IP_TRUTH_SOURCE', 'internet-ip'),
        'CURATOR_PROTO': environ.get('CURATOR_PROTO', 'http'),
        'CURATOR_HOSTNAME': environ.get('CURATOR_HOSTNAME', 'ipcurator'),
        'CURATOR_PORT': environ.get('CURATOR_PORT', '5000'),
        'CURATOR_PATH': environ.get('CURATOR_PATH', '/v1/telemetry'),
        'MY_POD_NAMESPACE': environ.get('MY_POD_NAMESPACE', ''),
        'STARTUP_DELAY': int(environ.get('STARTUP_DELAY', '0')),
        'TRANSMIT_MIN_INTERVAL_DELAY': int(environ.get('TRANSMIT_MIN_INTERVAL_DELAY', 60)),
        'TRANSMIT_MAX_INTERVAL_DELAY': int(environ.get('TRANSMIT_MAX_INTERVAL_DELAY', 180)),
        'DEFAULT_REQUEST_TIMEOUT': int(environ.get('DEFAULT_REQUEST_TIMEOUT', 5))
    }
    __setters = ['LOGLEVEL']

    @staticmethod
    def config(name):
        return App.__conf[name]

    @staticmethod
    def set(name, value):
        if name in App.__setters:
            App.__conf[name] = value
        else:
            raise NameError('Name not accepted in set() method')


if __name__ == '__main__':
    """
    a simple local test
    """
    print(f'{App.config("LOGLEVEL")}')
    App.set('LOGLEVEL', 'DEBUG')
    print(f'{App.config("LOGLEVEL")}')
