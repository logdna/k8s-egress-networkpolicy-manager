from ipcollector import __version__
from setuptools import setup, find_packages
from sys import path
from os import environ

path.insert(0, '.')

NAME = 'ipcollector'

if __name__ == '__main__':

    with open(environ.get('REQUIREMENTS_TXT', 'requirements.txt')) as f:
        requirements = f.read().splitlines()

    setup(
        name=NAME,
        version=__version__,
        author='Jonathan Kelley',
        author_email='jonathan.kelley@logdna.com',
        url='https://github.com/logdna/k8s-egress-networkpolicy-manager',
        license='ASLv2',
        packages=find_packages(),
        package_dir={NAME: NAME},
        description='ipcollector - Daemon that collects and forwards node/host IP telemetry to your ip-curator service. A component of k8s-egress-policy-manager',

        install_requires=requirements,

        entry_points={
            'console_scripts': ['ipcollector = ipcollector.app:main'],
        }
    )
