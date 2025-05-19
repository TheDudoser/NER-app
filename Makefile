.PHONY: init

DOCKER_COMPOSE=docker compose
PYTHON_SERVICE=backend

init: .env install

.env:
	@cp .env.dist .env

install:
	@$(DOCKER_COMPOSE) exec $(PYTHON_SERVICE) pip install --no-cache-dir -r requirements.txt

freeze:
	@$(DOCKER_COMPOSE) exec $(PYTHON_SERVICE) pip freeze > requirements.txt
