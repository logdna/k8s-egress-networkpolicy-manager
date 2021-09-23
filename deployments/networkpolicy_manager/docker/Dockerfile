ARG PYTHON_VERSION=latest

FROM logdna/tooling-python:${PYTHON_VERSION}

USER root

ARG BUILD_VERSION

ARG OCI_AUTHORS
ARG OCI_CREATED
ARG OCI_DESCRIPTION
ARG OCI_SOURCE
ARG OCI_TITLE
ARG OCI_URL
ARG OCI_VCS_REF

LABEL org.opencontainers.image.title="${OCI_TITLE}"
LABEL org.opencontainers.image.description="${OCI_DESCRIPTION}"
LABEL org.opencontainers.image.url="${OCI_URL}"
LABEL org.opencontainers.image.source="${OCI_SOURCE}"
LABEL org.opencontainers.image.authors="${OCI_AUTHORS}"
LABEL org.opencontainers.image.vendor="LogDNA, Inc."
LABEL org.opencontainers.image.created="${OCI_CREATED}"
LABEL org.opencontainers.image.version="${BUILD_VERSION}"
LABEL org.opencontainers.image.revision="${OCI_VCS_REF}"

RUN mkdir -p /src/dist

WORKDIR /src

COPY . /src

RUN useradd -u 10001 networkpolicymanager

RUN python setup.py install

USER networkpolicymanager

CMD ["networkpolicy_manager"]
