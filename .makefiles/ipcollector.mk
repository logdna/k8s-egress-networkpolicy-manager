
DOCKERFILE_IPCOLLECTOR_PATH ?= deployments/ipcollector/docker
DOCKER_PRIVATE_IMAGE_IPCOLLECTOR ?= us.gcr.io/logdna-k8s/ipcollector
DOCKER_PUBLIC_IMAGE_IPCOLLECTOR ?= docker.io/logdna/ipcollector
DOCKERFILE_IPCOLLECTOR ?= $(DOCKERFILE_IPCOLLECTOR_PATH)/Dockerfile
APP_COLLECTOR_SRC ?= src/ipcollector
APP_IPCOLLECTOR_VERSION ?= $(shell grep '__version__ =' src/ipcollector/ipcollector/__init__.py | cut -d' ' -f3 | xargs)


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
APP_IPCOLLECTOR_MAJOR_VERSION ?= $(shell echo $(APP_IPCOLLECTOR_VERSION) | cut -f1 -d'.')
APP_IPCOLLECTOR_MINOR_VERSION ?= $(shell echo $(APP_IPCOLLECTOR_VERSION) | cut -f1-2 -d'.')
APP_IPCOLLECTOR_PATCH_VERSION ?= $(shell echo $(APP_IPCOLLECTOR_VERSION))
APP_IPCOLLECTOR_BUILD_VERSION := '$(APP_IPCOLLECTOR_PATCH_VERSION)-$(BUILD_DATESTAMP)'

# Docker Variables - networkpolicymanager
# Build out a full list of tags for the image build
DOCKER_TAGS_IPCOLLECTOR := $(GIT_SHA1) $(APP_IPCOLLECTOR_VERSION) $(APP_IPCOLLECTOR_MAJOR_VERSION) $(APP_IPCOLLECTOR_MINOR_VERSION)
DOCKER_BUILD_TAGS_IPCOLLECTOR := $(addprefix --tag $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):,$(DOCKER_TAGS_IPCOLLECTOR))


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
build:: build-image-ipcollector

.PHONY:build-image-ipcollector
build-image-ipcollector::
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

.PHONY: publish
publish:: publish-image-gcr publish-image-dockerhub

.PHONY:publish-image-gcr
publish-image-gcr::
ifneq (,$(DOCKERFILE_IPCOLLECTOR))
	@for version in $(DOCKER_TAGS_IPCOLLECTOR); do \
		echo "publish: ipcollector (gcr)"; \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$(GIT_SHA1) $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$${version}; \
		$(DOCKER) push $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$${version}; \
	done
endif

.PHONY:publish-image-dockerhub
publish-image-dockerhub::
ifneq (,$(DOCKERFILE_IPCOLLECTOR))
	@for version in $(DOCKER_TAGS_IPCOLLECTOR); do \
		echo "publish: ipcollector (docker.io)"; \
		$(DOCKER) tag $(DOCKER_PRIVATE_IMAGE_IPCOLLECTOR):$(GIT_SHA1) $(DOCKER_PUBLIC_IMAGE_IPCOLLECTOR):$${version}; \
		$(DOCKER) push $(DOCKER_PUBLIC_IMAGE_IPCOLLECTOR):$${version}; \
	done
endif

.PHONY:test
test:: test-pytest-ipcurator

.PHONY:test-pytest-ipcurator
test-pytest-ipcurator::         ## Runs pytest suite
	$(DOCKER) run -v $(PWD):/workdir:Z -v $(PWD):/data:Z $(PYTHON_IMAGE):$(PYTHON_VERSION) /bin/bash -c 'bash /data/scripts/test_ipcurator.sh'


#     @if [ "test" = "test" ]; then\
#         echo "Hello world";\
#     fi