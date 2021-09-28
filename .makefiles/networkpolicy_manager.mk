

DOCKERFILE_NETWORKPOLICYMANAGER_PATH ?= deployments/networkpolicy_manager/docker
DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER ?= us.gcr.io/logdna-k8s/networkpolicy_manager
DOCKER_PUBLIC_IMAGE_NETWORKPOLICYMANAGER ?= docker.io/logdna/networkpolicy_manager
DOCKERFILE_NETWORKPOLICYMANAGER ?= $(DOCKERFILE_NETWORKPOLICYMANAGER_PATH)/Dockerfile
APP_NETWORKPOLICYMANAGER_SRC ?= src/networkpolicy_manager
APP_NETWORKPOLICYMANAGER_VERSION ?= $(shell REQUIREMENTS_TXT=./src/networkpolicy_manager/requirements.txt; python3 src/networkpolicy_manager/setup.py --version)

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



# Docker Variables - networkpolicymanager
# Build out a full list of tags for the image build
DOCKER_TAGS_NETWORKPOLICYMANAGER := $(GIT_SHA1) $(APP_NETWORKPOLICYMANAGER_RELEASE_VERSION)
ifneq ("$(BUILD_VERSION)", "$(APP_NETWORKPOLICYMANAGER_RELEASE_VERSION)")
	DOCKER_TAGS_NETWORKPOLICYMANAGER := $(DOCKER_TAGS_NETWORKPOLICYMANAGER) $(APP_NETWORKPOLICYMANAGER_MINOR_VERSION) $(APP_NETWORKPOLICYMANAGER_MAJOR_VERSION)
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

.PHONY: build
build:: build-image-networkpolicy_manager

.PHONY:build-image-networkpolicy_manager
build-image-networkpolicy_manager::
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

.PHONY: publish
publish:: publish-image-gcr

.PHONY:publish-image-gcr
publish-image-gcr::
ifneq (,$(DOCKERFILE_NETWORKPOLICYMANAGER))
	echo "publish: networkpolicymanager (gcr)"
	@for version in $(DOCKER_TAGS_NETWORKPOLICYMANAGER); do \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$(GIT_SHA1) $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
		$(DOCKER) push $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
	done
endif

.PHONY:publish-image-dockerhub
publish-image-dockerhub::
ifneq (,$(DOCKERFILE_NETWORKPOLICYMANAGER))
	@for version in $(DOCKER_TAGS_NETWORKPOLICYMANAGER); do \
	echo "publish: networkpolicymanager (docker.io)"; \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_NETWORKPOLICYMANAGER):$(GIT_SHA1) $(DOCKER_PUBLIC_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
		$(DOCKER) push $(DOCKER_PUBLIC_IMAGE_NETWORKPOLICYMANAGER):$${version}; \
	done
endif

.PHONY:test
test:: test-pytest-networkpolicy_manager

.PHONY:test-pytest-networkpolicy_manager
test-pytest-networkpolicy_manager::         ## Runs pytest suite
	$(DOCKER) run -v $(PWD):/workdir:Z -v $(PWD):/data:Z $(PYTHON_IMAGE):$(PYTHON_VERSION) /bin/bash -c 'bash /data/scripts/test_networkpolicy_manager.sh'
