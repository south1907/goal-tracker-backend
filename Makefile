.PHONY: help install dev test lint format clean docker-up docker-down migrate seed clear-data clear-all clear-user

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install

dev: ## Start development server
	poetry run python run.py

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=app --cov-report=html

lint: ## Run linting
	poetry run ruff check app tests
	poetry run mypy app

format: ## Format code
	poetry run black app tests
	poetry run isort app tests
	poetry run ruff check --fix app tests

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

migrate: ## Run database migrations
	docker-compose run --rm migration

seed: ## Create seed data
	docker-compose run --rm seed

clear-data: ## Clear all test data (keeps users)
	poetry run python clear_test_data.py

clear-all: ## Clear all test data including users
	poetry run python clear_test_data.py --delete-users

clear-user: ## Clear data for specific user (usage: make clear-user EMAIL=user@example.com)
	poetry run python clear_test_data.py --user $(EMAIL)

setup: install ## Setup development environment
	cp env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Then run: make docker-up && make migrate && make seed"
