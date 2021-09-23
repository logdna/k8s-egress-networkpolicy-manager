#!/bin/bash
pushd /data/src/ipcurator
	pip3 install .
popd

export PYTHONPATH=/data/src/ipcurator

pytest /data/tests/ipcurator/test_app_config.py -o junit_family=xunit2 --junitxml=./reports/py${PYTHON_VERSION}_ipcurator0.junit.xml
pytest /data/tests/ipcurator/test_singleton.py -o junit_family=xunit2 --junitxml=./reports/py${PYTHON_VERSION}_ipcurator1.junit.xml

mkdir -p /data/reports
mv /usr/src/app/reports/*.xml /data/reports