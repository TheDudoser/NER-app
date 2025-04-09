DOCKER_IMAGE = ner-app:latest

DOCKER_RUN = docker run \
    --volume $$(pwd):/opt/workdir \
    --user "$$(id -u):$$(id -g)" \
    --env HOME=/tmp \
    --env XDG_CACHE_HOME=/tmp/.cache \
    --workdir /opt/workdir

PYTHON = $(DOCKER_RUN) $(DOCKER_IMAGE) python
PIP = $(DOCKER_RUN) $(DOCKER_IMAGE) pip
