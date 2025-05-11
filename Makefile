.PHONY: init

DOCKER_COMPOSE=docker compose
PYTHON_SERVICE=backend

init: .env

.env:
	@cp .env.dist .env

freeze:
	@$(DOCKER_COMPOSE) exec $(PYTHON_SERVICE) pip freeze > requirements.txt
