from setuptools import setup, find_packages
from sys import path

from ipcurator import __version__
from os import environ

path.insert(0, '.')

NAME = 'ipcurator'

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
        description='ipcurator - REST server that processes queries about nodes in your cluster and presents the egress IP for a particular set of nodes. A component of k8s-egress-policy-manager',

        install_requires=requirements,

        entry_points={
            'console_scripts': ['ipcurator = ipcurator.app:main'],
        }
    )