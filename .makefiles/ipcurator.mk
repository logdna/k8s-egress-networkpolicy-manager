

DOCKERFILE_IPCURATOR_PATH ?= deployments/ipcurator/docker
DOCKER_IMAGE_IPCURATOR ?= us.gcr.io/logdna-k8s/ipcurator
DOCKER_PUBLIC_IMAGE_IPCURATOR ?= docker.io/logdna/ipcurator
DOCKERFILE_IPCURATOR ?= $(DOCKERFILE_IPCURATOR_PATH)/Dockerfile
APP_IPCURATOR_SRC ?= src/ipcurator
APP_IPCURATOR_VERSION ?= $(grep '__version__ =' src/ipcurator/ipcurator/__init__.py | cut -d' ' -f3 | xargs)

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


# Docker Variables - ipcurator
# Build out a full list of tags for the image build
DOCKER_TAGS_IPCURATOR := $(GIT_SHA1) $(APP_IPCURATOR_RELEASE_VERSION)
ifneq ("$(BUILD_VERSION)", "$(APP_IPCURATOR_RELEASE_VERSION)")
	DOCKER_TAGS_IPCURATOR := $(DOCKER_TAGS_IPCURATOR) $(APP_IPCURATOR_MINOR_VERSION) $(APP_IPCURATOR_MAJOR_VERSION)
endif
# This creates a `docker build` cli-compatible list of the tags
DOCKER_BUILD_TAGS_IPCURATOR := $(addprefix --tag $(DOCKER_IMAGE_IPCURATOR):,$(DOCKER_TAGS_IPCURATOR))

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
build:: build-image-ipcurator

.PHONY:build-image-ipcurator
build-image-ipcurator::
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

.PHONY: publish
publish:: publish-image-gcr

.PHONY:publish-image-gcr
publish-image-gcr::
ifneq (,$(DOCKERFILE_IPCURATOR))
	echo "publish: ipcurator (gcr)"
	@for version in $(DOCKER_TAGS_IPCURATOR); do \
		$(DOCKER) tag $(DOCKER_IMAGE_IPCURATOR):$(GIT_SHA1) $(DOCKER_IMAGE_IPCURATOR):$${version}; \
		$(DOCKER) push $(DOCKER_IMAGE_IPCURATOR):$${version}; \
	done
endif

.PHONY:publish-image-dockerhub
publish-image-dockerhub::
ifneq (,$(DOCKERFILE_IPCURATOR))
	@for version in $(DOCKER_TAGS_IPCURATOR); do \
	echo "publish: ipcurator (docker.io)"; \
		$(DOCKER) tag $(DOCKER_IMAGE_IPCURATOR):$(GIT_SHA1) $(DOCKER_PUBLIC_IMAGE_IPCURATOR):$${version}; \
		$(DOCKER) push $(DOCKER_PUBLIC_IMAGE_IPCURATOR):$${version}; \
	done
endif

.PHONY:test
test:: test-pytest-ipcollector

.PHONY:test-pytest-ipcollector
test-pytest-ipcollector::         ## Runs pytest suite
	$(DOCKER) run -v $(PWD):/workdir:Z -v $(PWD):/data:Z $(PYTHON_IMAGE):$(PYTHON_VERSION) /bin/bash -c 'bash /data/scripts/test_ipcollector.sh'
