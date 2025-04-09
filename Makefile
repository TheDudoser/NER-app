-include local.mk

PYTHON ?= python
PIP ?= pip

build:
	docker build --no-cache -t ner-app .

install:
	@$(PIP) install -r requirements.txt

install-no-cache:
	@$(PIP) install --no-cache-dir -r requirements.txt

start:
	docker run -u=$(id -u $USER):$(id -g $USER) -e DISPLAY=$IP:0 -v /tmp/.X11-unix:/tmp/.X11-unix:rw --rm -it ner-app

# TODO
lint:
	@$(BUF) lint

# TODO
test:
	pass
