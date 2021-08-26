#!/usr/bin/env python3
from os import environ
from os import path
from yaml import Loader, load
import yaml


def str2bool(v):
    return v.lower() in ('yes', 'true', 't', '1')


def get_config_path():
    if path.exists('/etc/ipcurator-sources.yaml'):
        return '/etc/ipcurator-sources.yaml'
    else:
        return 'ipcurator-sources.yaml'


def load_config():
    with open(get_config_path(), 'r') as f:
        return load(f, Loader=Loader)


class App:
    __conf = {
        'LOGLEVEL': environ.get('LOGLEVEL', 'INFO'),
        'LOGDATEFMT': environ.get('LOGDATEFMT', '%Y-%m-%d %H:%M:%S'),
        'LOGFORMAT': environ.get('LOGFORMAT', '%(asctime)s %(levelname)-8s %(message)s'),
        'DEFAULT_REFRESH_RATE': int(environ.get('DEFAULT_REFRESH_RATE', 5)),
        'DEFAULT_POLICY_NAME_PREFIX': environ.get('DEFAULT_POLICY_NAME_PREFIX', 'networkpolicy-manager-'),
        'CONFIGMAP_FROM_DISK': load_config(),
        'STRICT_CIDRS': str2bool(environ.get('STRICT_CIDRS', 'false')),
    }
    __setters = ['LOGLEVEL', 'CONFIGMAP_FROM_DISK']

    @staticmethod
    def config(name):
        return App.__conf[name]

    @staticmethod
    def set(name, value):
        if name in App.__setters:
            App.__conf[name] = value
        else:
            raise NameError("Name not accepted in set() method")


if __name__ == "__main__":
    App.config("LOGLEVEL")
