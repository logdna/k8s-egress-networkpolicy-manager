#!/usr/bin/env python3
from os import environ


def str2bool(v):
    return v.lower() in ('yes', 'true', 't', '1')


class App:
    __conf = {
        'ALLOWED_NAMESPACES': environ.get('ALLOWED_NAMESPACES', '*').split(','),
        'CALCULATE_EFFICIENT_CIDRS': str2bool(environ.get('CALCULATE_EFFICIENT_CIDRS', 'true')),
        'LOGLEVEL': environ.get('LOGLEVEL', 'INFO'),
        'LOGDATEFMT': environ.get('LOGDATEFMT', '%Y-%m-%d %H:%M:%S'),
        'LOGFORMAT': environ.get('LOGFORMAT', '%(asctime)s %(levelname)-8s %(message)s'),
        'RESPONSE_NOTE': environ.get('RESPONSE_NOTE', None),
        'REVEAL_VERSION_ON_INDEX_PAGE': str2bool(environ.get('REVEAL_VERSION_ON_INDEX_PAGE', 'true')),
        'UPDATE_EFFICIENT_CIDR_INTERVAL': int(environ.get('UPDATE_EFFICIENT_CIDR_INTERVAL', '1800'))
    }
    __setters = ['ALLOWED_NAMESPACES', 'LOGLEVEL']

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
