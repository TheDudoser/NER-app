SHELL := /bin/bash

PYTHON = python3
PIP = pip3

init: create_venv install

create_venv:
	@$(PYTHON) -m venv .venv
	source .venv/bin/activate

install:
	@$(PIP) install -r requirements.txt

freeze:
	@$(PYTHON) -m pip freeze > requirements.txt
