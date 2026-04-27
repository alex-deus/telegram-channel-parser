.PHONY: lint update-isort install

HOST ?= leaker

lint:  ## Run pre-commit on all files
	@pre-commit run --all-files

update-isort:  ## Update iSort config at pyproject.toml
	@seed-isort-config

install:  ## Install package and pre-commit hooks
	@pip install poetry
	@poetry install --no-root
	@pre-commit install

cp:
	@rsync -avz \
 		--exclude 'tmp' \
 		--exclude '.env' \
 		--exclude '.venv' \
 		--exclude '.idea' \
 		--exclude '.DS_Store' \
 		--exclude '.git' \
 		--exclude '*.pyc' \
 		--exclude '__pycache__' \
 		--exclude 'data' \
 		--exclude 'tmp' \
 		. ${HOST}:~/tg-parser
