.PHONY: init

DOCKER_COMPOSE=docker compose
PYTHON_SERVICE=backend

.env:
	@cp .env.dist .env

install:
	@$(DOCKER_COMPOSE) exec $(PYTHON_SERVICE) pip install --no-cache-dir -r requirements.txt

freeze:
	@$(DOCKER_COMPOSE) exec $(PYTHON_SERVICE) pip freeze > requirements.txt

test:
	@$(DOCKER_COMPOSE) exec $(PYTHON_SERVICE) python -m unittest discover -s tests -p "test*.py"
