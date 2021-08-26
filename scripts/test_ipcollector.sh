#!/bin/bash
pushd /data/src/ipcollector
	pip3 install .
popd

export PYTHONPATH=/data/src/ipcollector

pytest /data/tests/ipcollector -o junit_family=xunit2 --junitxml=./reports/py${PYTHON_VERSION}_ipcollector.junit.xml

mkdir -p /data/reports
mv /usr/src/app/reports/*.xml /data/reports