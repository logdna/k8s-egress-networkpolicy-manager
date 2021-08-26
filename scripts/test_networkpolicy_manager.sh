#!/bin/bash
pushd /data/src/networkpolicy_manager
	pip3 install .
popd

export PYTHONPATH=/data/src/networkpolicy_manager
pushd /data
	pytest /data/tests/networkpolicy_manager -o junit_family=xunit2 --junitxml=./reports/py${PYTHON_VERSION}_networkpolicy_manager.junit.xml
popd

