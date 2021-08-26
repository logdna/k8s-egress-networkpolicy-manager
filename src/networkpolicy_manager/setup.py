from setuptools import setup, find_packages
from sys import path

from networkpolicy_manager import __version__
from os import environ

path.insert(0, '.')

NAME = 'networkpolicy_manager'

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
        description='networkpolicy_manager - stateless deployment that runs within your cluster and manages sets of ingress networkpolicy resources dynamically ',

        install_requires=requirements,

        entry_points={
            'console_scripts': ['networkpolicy_manager = networkpolicy_manager.app:main'],
        }
    )