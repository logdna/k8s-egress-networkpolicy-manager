# Makefile Version 2021041501
#
# Source in repository specific environment variables
-include .config.mk

DOCKERFILE_IPCOLLECTOR_PATH ?= deployments/ipcollector/docker
DOCKER_PRIVATE_IMAGE_IPCOLLECTOR ?= us.gcr.io/logdna-k8s/ipcollector
DOCKER_PUBLIC_IMAGE_IPCOLLECTOR ?= docker.io/logdna/ipcollector
DOCKERFILE_IPCOLLECTOR ?= $(DOCKERFILE_IPCOLLECTOR_PATH)/Dockerfile
APP_COLLECTOR_SRC ?= src/ipcollector

DOCKERFILE_IPCURATOR_PATH ?= deployments/ipcurator/docker
DOCKER_IMAGE_IPCURATOR ?= us.gcr.io/logdna-k8s/ipcurator
DOCKER_PUBLIC_IMAGE_IPCURATOR ?= docker.io/logdna/ipcurator
DOCKERFILE_IPCURATOR ?= $(DOCKERFILE_IPCURATOR_PATH)/Dockerfile
APP_IPCURATOR_SRC ?= src/ipcurator

DOCKERFILE_NETWORKPOLICYMANAGER_PATH ?= deployments/networkpolicy_manager/docker
DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER ?= us.gcr.io/logdna-k8s/networkpolicy_manager
DOCKER_PUBLIC_IMAGE_NETWORKPOLICYMANAGER ?= docker.io/logdna/networkpolicy_manager
DOCKERFILE_NETWORKPOLICYMANAGER ?= $(DOCKERFILE_NETWORKPOLICYMANAGER_PATH)/Dockerfile
APP_NETWORKPOLICYMANAGER_SRC ?= src/networkpolicy_manager

# Provide standard defaults - set overrides in .config.mk
SHELL=/bin/bash -o pipefail
ALWAYS_TIMESTAMP_VERSION ?= false
DOCKER_BUILD_ALWAYS_PULL ?= true
TMP_DIR ?= tmp
BUILD_ENV ?= $(TMP_DIR)/build-env

# get the app versions for each python app
APP_IPCOLLECTOR_VERSION ?= $(grep '__version__ =' src/ipcollector/ipcollector/__init__.py | cut -d' ' -f3 | xargs)
APP_IPCURATOR_VERSION ?= $(grep '__version__ =' src/ipcurator/ipcurator/__init__.py | cut -d' ' -f3 | xargs)
APP_NETWORKPOLICYMANAGER_VERSION ?= $(grep '__version__ =' src/networkpolicy_manager/networkpolicy_manager/__init__.py | cut -d' ' -f3 | xargs)


## Define sources for rendering and templating
GIT_SHA1 ?= $(shell git log --pretty=format:'%h' -n 1)
GIT_BRANCH ?= $(shell git branch --show-current)
GIT_URL ?= $(shell git remote get-url origin)
GIT_INFO ?= $(TMP_DIR)/.git-info.$(GIT_SHA1)
BUILD_URL ?= localbuild://${USER}@$(shell uname -n | sed "s/'//g")
BUILD_DATESTAMP ?= $(shell date -u '+%Y%m%dT%H%M%SZ')

KUBECTL_VERSION ?= 1.18.2
export PYTHON_VERSION ?= 3.9
PYTHON_IMAGE ?= logdna/tooling-python

# Define commands via docker
DOCKER ?= docker
DOCKER_DATADIR = -v $(PWD):/data:Z
DOCKER_WORKDIR = -v $(PWD):/workdir:Z
DOCKER_RUN := $(DOCKER) run --rm -i
ENVSUBST_COMMAND := $(DOCKER_RUN) --env-file=$(BUILD_ENV) $(DOCKER_DATADIR) bhgedigital/envsubst envsubst "$$(printf '$${%s} ' $$(cut -f1 -d'=' ${BUILD_ENV}))"
YAMLLINT_COMMAND := $(DOCKER_RUN) $(DOCKER_DATADIR) cytopia/yamllint:latest
HADOLINT_COMMAND := $(DOCKER_RUN) $(DOCKER_WORKDIR) -w /workdir hadolint/hadolint:v1.8.0 hadolint --ignore SC2086

PYTHON_RUN := $(DOCKER_RUN) -v $(PWD):/usr/src/app:Z $(PYTHON_IMAGE):$(PYTHON_VERSION)
PYTHON ?= $(PYTHON_RUN) python
PYTEST ?= $(PYTHON_RUN) pytest
PYCODESTYLE ?= $(PYTHON_RUN) pycodestyle .
AUTOPEP8 ?= $(PYTHON_RUN) autopep8

PIP ?= $(PYTHON) -m pip
PIP_INSTALL ?= $(PIP) install --upgrade --user
PIP_UNINSTALL := $(PIP) uninstall -y

# ipcollector version stuff
# ------
ifeq ("$(BUILD_ENV)", "$(wildcard $(BUILD_ENV))")
	# if tmp/build-env exists on disk, use it
	include $(BUILD_ENV)
else ifneq "$(APP_IPCOLLECTOR_VERSION)" ""
	# Tooling repositories are centered around the version of an
	# upstream off the shelf application. When working with that
	# type of application we want to add their version unmodified
	# as a prefix when creating a DATESTAMP based internal
	# release version.
	APP_IPCOLLECTOR_MAJOR_VERSION = $(shell echo $(APP_IPCOLLECTOR_VERSION) | cut -f1 -d'.')
	APP_IPCOLLECTOR_MINOR_VERSION = $(shell echo $(APP_IPCOLLECTOR_VERSION) | cut -f1-2 -d'.')
	APP_IPCOLLECTOR_PATCH_VERSION = $(shell echo $(APP_IPCOLLECTOR_VERSION))
	APP_IPCOLLECTOR_BUILD_VERSION := $(APP_IPCOLLECTOR_PATCH_VERSION)-$(BUILD_DATESTAMP)
	ifneq ("$(GIT_BRANCH)", $(filter "$(GIT_BRANCH)", "master" "main"))
		APP_IPCOLLECTOR_RELEASE_VERSION := $(APP_IPCOLLECTOR_BUILD_VERSION)
	else ifeq ("$(ALWAYS_TIMESTAMP_VERSION)", "true")
		APP_IPCOLLECTOR_RELEASE_VERSION := $(APP_IPCOLLECTOR_BUILD_VERSION)
	else
		APP_IPCOLLECTOR_RELEASE_VERSION := $(APP_IPCOLLECTOR_PATCH_VERSION)
	endif
else
	# For repositories, like control or tooling, that don't have their own
	# versioning, we default to a datestamp format. For tooling
	# repositories we want the prefix of version, which is handled above.
	# TODO: Add warning that APP_VERSION WAS EMPTY so defaulting to CalVer
	# based timestamp version
	APP_IPCOLLECTOR_BUILD_VERSION = $(BUILD_DATESTAMP)
	APP_IPCOLLECTOR_APP_IPCOLLECTOR_RELEASE_VERSION := $(APP_IPCOLLECTOR_BUILD_VERSION)
endif

# ipcurator version stuff
# ------
ifeq ("$(BUILD_ENV)", "$(wildcard $(BUILD_ENV))")
	# if tmp/build-env exists on disk, use it
	include $(BUILD_ENV)
else ifneq "$(APP_IPCURATOR_VERSION)" ""
	# Tooling repositories are centered around the version of an
	# upstream off the shelf application. When working with that
	# type of application we want to add their version unmodified
	# as a prefix when creating a DATESTAMP based internal
	# release version.
	APP_IPCURATOR_MAJOR_VERSION = $(shell echo $(APP_IPCURATOR_VERSION) | cut -f1 -d'.')
	APP_IPCURATOR_MINOR_VERSION = $(shell echo $(APP_IPCURATOR_VERSION) | cut -f1-2 -d'.')
	APP_IPCURATOR_PATCH_VERSION = $(shell echo $(APP_IPCURATOR_VERSION))
	APP_IPCURATOR_BUILD_VERSION := $(APP_IPCURATOR_PATCH_VERSION)-$(BUILD_DATESTAMP)
	ifneq ("$(GIT_BRANCH)", $(filter "$(GIT_BRANCH)", "master" "main"))
		APP_IPCURATOR_RELEASE_VERSION := $(APP_IPCURATOR_BUILD_VERSION)
	else ifeq ("$(ALWAYS_TIMESTAMP_VERSION)", "true")
		APP_IPCURATOR_RELEASE_VERSION := $(APP_IPCURATOR_BUILD_VERSION)
	else
		APP_IPCURATOR_RELEASE_VERSION := $(APP_IPCURATOR_PATCH_VERSION)
	endif
else
	# For repositories, like control or tooling, that don't have their own
	# versioning, we default to a datestamp format. For tooling
	# repositories we want the prefix of version, which is handled above.
	# TODO: Add warning that APP_VERSION WAS EMPTY so defaulting to CalVer
	# based timestamp version
	APP_IPCURATOR_BUILD_VERSION = $(BUILD_DATESTAMP)
	APP_IPCURATOR_APP_IPCURATOR_RELEASE_VERSION := $(APP_IPCURATOR_BUILD_VERSION)
endif


# networkpolicymanager version stuff
# ------
ifeq ("$(BUILD_ENV)", "$(wildcard $(BUILD_ENV))")
	# if tmp/build-env exists on disk, use it
	include $(BUILD_ENV)
else ifneq "$(APP_NETWORKPOLICYMANAGER_VERSION)" ""
	# Tooling repositories are centered around the version of an
	# upstream off the shelf application. When working with that
	# type of application we want to add their version unmodified
	# as a prefix when creating a DATESTAMP based internal
	# release version.
	APP_NETWORKPOLICYMANAGER_MAJOR_VERSION = $(shell echo $(APP_NETWORKPOLICYMANAGER_VERSION) | cut -f1 -d'.')
	APP_NETWORKPOLICYMANAGER_MINOR_VERSION = $(shell echo $(APP_NETWORKPOLICYMANAGER_VERSION) | cut -f1-2 -d'.')
	APP_NETWORKPOLICYMANAGER_PATCH_VERSION = $(shell echo $(APP_NETWORKPOLICYMANAGER_VERSION))
	APP_NETWORKPOLICYMANAGER_BUILD_VERSION := $(APP_NETWORKPOLICYMANAGER_PATCH_VERSION)-$(BUILD_DATESTAMP)
	ifneq ("$(GIT_BRANCH)", $(filter "$(GIT_BRANCH)", "master" "main"))
		APP_NETWORKPOLICYMANAGER_RELEASE_VERSION := $(APP_NETWORKPOLICYMANAGER_BUILD_VERSION)
	else ifeq ("$(ALWAYS_TIMESTAMP_VERSION)", "true")
		APP_NETWORKPOLICYMANAGER_RELEASE_VERSION := $(APP_NETWORKPOLICYMANAGER_BUILD_VERSION)
	else
		APP_NETWORKPOLICYMANAGER_RELEASE_VERSION := $(APP_NETWORKPOLICYMANAGER_PATCH_VERSION)
	endif
else
	# For repositories, like control or tooling, that don't have their own
	# versioning, we default to a datestamp format. For tooling
	# repositories we want the prefix of version, which is handled above.
	# TODO: Add warning that APP_VERSION WAS EMPTY so defaulting to CalVer
	# based timestamp version
	APP_NETWORKPOLICYMANAGER_BUILD_VERSION = $(BUILD_DATESTAMP)
	APP_NETWORKPOLICYMANAGER_APP_NETWORKPOLICYMANAGER_RELEASE_VERSION := $(APP_NETWORKPOLICYMANAGER_BUILD_VERSION)
endif


# Docker Variables - ipcollector
# Build out a full list of tags for the image build
DOCKER_TAGS_IPCOLLECTOR := $(GIT_SHA1) $(APP_IPCOLLECTOR_RELEASE_VERSION)
ifneq ("$(BUILD_VERSION)", "$(APP_IPCOLLECTOR_RELEASE_VERSION)")
	DOCKER_TAGS_IPCOLLECTOR := $(DOCKER_TAGS_IPCOLLECTOR) $(MINOR_VERSION) $(MAJOR_VERSION)
endif
# This creates a `docker build` cli-compatible list of the tags
DOCKER_BUILD_TAGS_IPCOLLECTOR := $(addprefix --tag $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):,$(DOCKER_TAGS_IPCOLLECTOR))


# Docker Variables - ipcurator
# Build out a full list of tags for the image build
DOCKER_TAGS_IPCURATOR := $(GIT_SHA1) $(APP_IPCURATOR_RELEASE_VERSION)
ifneq ("$(BUILD_VERSION)", "$(APP_IPCURATOR_RELEASE_VERSION)")
	DOCKER_TAGS_IPCURATOR := $(DOCKER_TAGS_IPCURATOR) $(MINOR_VERSION) $(MAJOR_VERSION)
endif
# This creates a `docker build` cli-compatible list of the tags
DOCKER_BUILD_TAGS_IPCURATOR := $(addprefix --tag $(DOCKER_IMAGE_IPCURATOR):,$(DOCKER_TAGS_IPCURATOR))


# Docker Variables - networkpolicymanager
# Build out a full list of tags for the image build
DOCKER_TAGS_NETWORKPOLICYMANAGER := $(GIT_SHA1) $(APP_NETWORKPOLICYMANAGER_RELEASE_VERSION)
ifneq ("$(BUILD_VERSION)", "$(APP_NETWORKPOLICYMANAGER_RELEASE_VERSION)")
	DOCKER_TAGS_NETWORKPOLICYMANAGER := $(DOCKER_TAGS_NETWORKPOLICYMANAGER) $(MINOR_VERSION) $(MAJOR_VERSION)
endif
# This creates a `docker build` cli-compatible list of the tags
DOCKER_BUILD_TAGS_NETWORKPOLICYMANAGER := $(addprefix --tag $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):,$(DOCKER_TAGS_NETWORKPOLICYMANAGER))

# Adjust docker build behaviors
ifeq ("$(DOCKER_BUILD_ALWAYS_PULL)", "true")
	DOCKER_BUILD_OPTS += --pull
endif
ifeq ("$(DOCKER_BUILD_NO_CACHE)", "true")
	DOCKER_BUILD_OPTS += --no-cache=true
endif

# OCI Image metadata https://github.com/opencontainers/image-spec/blob/master/spec.md
# Can override any with ?= in .config.mk
OCI_AUTHORS ?= "LogDNA Engineering"
OCI_CREATED ?= $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
OCI_DESCRIPTION ?= ""
OCI_SOURCE ?= https://github.com/logdna/k8s-egress-networkpolicy-manager
APP_IPCOLLECTOR_OCI_TITLE ?= "answerbook/$(APP_COLLECTOR_NAME)"
OCI_URL ?= "https://logdna.com"

ARTIFACTDIR = ./artifacts
DISTDIR = $(ARTIFACTDIR)/dist
REPORTSDIR ?= ./reports

ifeq ("$(PYTHON_VERSION)", "")
$(error PYTHON_VERSION must be set)
endif

# Exports all variables for shell use
export

## How the help target works:
# To show up in the helps there must be 2 spaces between the : or last target and the ##
# To leave a target completely off dont do any of the above.
.PHONY:help
.SILENT:help
help:           ## Prints out a helpful description of each possible target
	@awk 'BEGIN {FS = ":.*?  +## "}; /^.+: .


.PHONY:clean
clean:             ## Cleanup the local checkout
	git clean -xdf --exclude=$(ARTIFACTDIR) --exclude=.python

.PHONY:clean-all
clean-all: clean   ## Cleanup up everything; including venv, tox, and artifacts
	git clean -Xdf

.PHONY:clean-docker
clean-docker: ## Clean update docker images
	-$(DOCKER) image ls | awk -v image="$(APP_COLLECTOR_NAME)" -v tag="$(GIT_SHA1)" '$$1~image && $$2==tag {print $$3}' | xargs ${DOCKER} rmi -f

.python:
	mkdir -p .python
	$(PIP_INSTALL) -r src/$(APP_COLLECTOR_NAME)/requirements.txt

$(DISTDIR) $(REPORTSDIR) $(TMP_DIR):
	mkdir -p $(@)

$(GIT_INFO): | $(TMP_DIR)
	@env | awk '!/TOKEN/ && /^GIT/ { print }' > $(@)

.PHONY:format
format: setup      ## Automatically pep8s, should be run purposefully
	$(AUTOPEP8) -v -i -r /usr/src/app --exclude=test_data.py --exclude=.python

.PHONY:build
build: build-python build-image

.PHONY:build-python
build-python: clean       ## Cleanly build python artifact
	$(PYTHON) setup.py build -f

.PHONY: build-image
build-image: build-image-ipcollector build-image-ipcurator build-image-networkpolicymanager

.PHONY:build-image-ipcollector
build-image-ipcollector:
ifneq (,$(DOCKERFILE_IPCOLLECTOR))
	@# only run if DOCKERFILE_IPCOLLECTOR isn't empty; control repos don't have one
	$(DOCKER) build $(APP_COLLECTOR_SRC) --rm -f $(DOCKERFILE_IPCOLLECTOR) \
		$(DOCKER_BUILD_TAGS_IPCOLLECTOR) \
		$(DOCKER_BUILD_OPTS) \
		--build-arg BUILD_VERSION=$(APP_IPCOLLECTOR_BUILD_VERSION) \
		--build-arg KUBECTL_VERSION=$(KUBECTL_VERSION) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg OCI_AUTHORS=$(OCI_AUTHORS) \
		--build-arg OCI_CREATED=$(OCI_CREATED) \
		--build-arg OCI_DESCRIPTION=$(OCI_DESCRIPTION) \
		--build-arg OCI_TITLE=$(APP_IPCOLLECTOR_OCI_TITLE) \
		--build-arg OCI_SOURCE=$(OCI_SOURCE) \
		--build-arg OCI_VCS_REF=$(GIT_SHA1)
endif

.PHONY:build-image-ipcurator
build-image-ipcurator:
ifneq (,$(DOCKERFILE_IPCURATOR))
	@# only run if DOCKERFILE_IPCURATOR isn't empty; control repos don't have one
	$(DOCKER) build $(APP_IPCURATOR_SRC) --rm -f $(DOCKERFILE_IPCURATOR) \
		$(DOCKER_BUILD_TAGS_IPCURATOR) \
		$(DOCKER_BUILD_OPTS) \
		--build-arg BUILD_VERSION=$(APP_IPCURATOR_BUILD_VERSION) \
		--build-arg KUBECTL_VERSION=$(KUBECTL_VERSION) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg OCI_AUTHORS=$(OCI_AUTHORS) \
		--build-arg OCI_CREATED=$(OCI_CREATED) \
		--build-arg OCI_DESCRIPTION=$(OCI_DESCRIPTION) \
		--build-arg OCI_TITLE=$(APP_IPCURATOR_OCI_TITLE) \
		--build-arg OCI_SOURCE=$(OCI_SOURCE) \
		--build-arg OCI_VCS_REF=$(GIT_SHA1)
endif

.PHONY:build-image-networkpolicymanager
build-image-networkpolicymanager:
ifneq (,$(DOCKERFILE_NETWORKPOLICYMANAGER))
	@# only run if DOCKERFILE_NETWORKPOLICYMANAGER isn't empty; control repos don't have one
	$(DOCKER) build $(APP_NETWORKPOLICYMANAGER_SRC) --rm -f $(DOCKERFILE_NETWORKPOLICYMANAGER) \
		$(DOCKER_BUILD_TAGS_NETWORKPOLICYMANAGER) \
		$(DOCKER_BUILD_OPTS) \
		--build-arg BUILD_VERSION=$(APP_NETWORKPOLICYMANAGER_BUILD_VERSION) \
		--build-arg KUBECTL_VERSION=$(KUBECTL_VERSION) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg OCI_AUTHORS=$(OCI_AUTHORS) \
		--build-arg OCI_CREATED=$(OCI_CREATED) \
		--build-arg OCI_DESCRIPTION=$(OCI_DESCRIPTION) \
		--build-arg OCI_TITLE=$(APP_NETWORKPOLICYMANAGER_OCI_TITLE) \
		--build-arg OCI_SOURCE=$(OCI_SOURCE) \
		--build-arg OCI_VCS_REF=$(GIT_SHA1)
endif

.PHONY: publish-image
publish-image: publish-image-gcr publish-image-dockerhub

.PHONY:publish-image-gcr
publish-image-gcr: ## Publish SemVer compliant releases to gcr
ifneq (,$(DOCKERFILE_IPCOLLECTOR))
	@for version in $(DOCKER_TAGS_IPCOLLECTOR); do \
		echo "publish: ipcollector (gcr)"; \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$(GIT_SHA1) $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$${version}; \
		$(DOCKER) push $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$${version}; \
	done
endif
ifneq (,$(DOCKERFILE_IPCURATOR))
	echo "publish: ipcurator (gcr)"
	@for version in $(DOCKER_TAGS_IPCURATOR); do \
		$(DOCKER) tag $(DOCKER_IMAGE_IPCURATOR):$(GIT_SHA1) $(DOCKER_IMAGE_IPCURATOR):$${version}; \
		$(DOCKER) push $(DOCKER_IMAGE_IPCURATOR):$${version}; \
	done
endif
ifneq (,$(DOCKERFILE_NETWORKPOLICYMANAGER))
	echo "publish: networkpolicymanager (gcr)"
	@for version in $(DOCKER_TAGS_NETWORKPOLICYMANAGER); do \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$(GIT_SHA1) $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
		$(DOCKER) push $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
	done
endif

.PHONY:publish-image-dockerhub
publish-image-dockerhub: ## Publish SemVer compliant releases to dockerhub
ifneq (,$(DOCKERFILE_IPCOLLECTOR))
	@for version in $(DOCKER_TAGS_IPCOLLECTOR); do \
		echo "publish: ipcollector (docker.io)"; \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$(GIT_SHA1) $(DOCKER_PUBLIC_IMAGE_IPCOLLECTOR):$${version}; \
		$(DOCKER) push $(DOCKER_PUBLIC_IMAGE_IPCOLLECTOR):$${version}; \
	done
endif
ifneq (,$(DOCKERFILE_IPCURATOR))
	@for version in $(DOCKER_TAGS_IPCURATOR); do \
	echo "publish: ipcurator (docker.io)"; \
		$(DOCKER) tag $(DOCKER_IMAGE_IPCURATOR):$(GIT_SHA1) $(DOCKER_PUBLIC_IMAGE_IPCURATOR):$${version}; \
		$(DOCKER) push $(DOCKER_PUBLIC_IMAGE_IPCURATOR):$${version}; \
	done
endif
ifneq (,$(DOCKERFILE_NETWORKPOLICYMANAGER))
	@for version in $(DOCKER_TAGS_NETWORKPOLICYMANAGER); do \
	echo "publish: networkpolicymanager (docker.io)"; \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$(GIT_SHA1) $(DOCKER_PUBLIC_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
		$(DOCKER) push $(DOCKER_PUBLIC_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
	done
endif

.PHONY:release-minor-ipcollector
release-minor: 
	. scripts/bump_minor_version ipcollector

.PHONY:test-pytest
test-pytest: test-pytest-ipcurator test-pytest-ipcollector test-pytest-networkpolicy_manager

.PHONY:test-pytest-ipcurator
test-pytest-ipcurator:         ## Runs pytest suite
	$(DOCKER) run -v $(PWD):/workdir:Z -v $(PWD):/data:Z $(PYTHON_IMAGE):$(PYTHON_VERSION) /bin/bash -c 'bash /data/scripts/test_ipcurator.sh'

.PHONY:test-pytest-ipcollector
test-pytest-ipcollector:         ## Runs pytest suite
	$(DOCKER) run -v $(PWD):/workdir:Z -v $(PWD):/data:Z $(PYTHON_IMAGE):$(PYTHON_VERSION) /bin/bash -c 'bash /data/scripts/test_ipcollector.sh'

.PHONY:test-pytest-networkpolicy_manager
test-pytest-networkpolicy_manager:         ## Runs pytest suite
	$(DOCKER) run -v $(PWD):/workdir:Z -v $(PWD):/data:Z $(PYTHON_IMAGE):$(PYTHON_VERSION) /bin/bash -c 'bash /data/scripts/test_networkpolicy_manager.sh'

.PHONY: test
test: test-pytest

# build the complete project into minikube
# this builds a local minikube integration environment
# it will force your kube namespace to minikube, and start minikube for you
# you must have minikube installed
.PHONY:minikube
minikube:
	bash scripts/build_minikube.sh


