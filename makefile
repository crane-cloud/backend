

# File names
DOCKER_DEV_COMPOSE_FILE := docker-compose.yml


help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

build-image: ## Build docker image
	@ ${INFO} "Building required docker images"
	@ docker compose -f $(DOCKER_DEV_COMPOSE_FILE) build api celery-worker
	@ ${INFO} "Image succesfully built"
	@ echo " "

start:build-image ## Start development server
	@ ${INFO} "starting local development server"
	@ docker compose -f $(DOCKER_DEV_COMPOSE_FILE) up

psql-connect:build-image ## Connect to psql
	@ ${INFO} "Connect to psql"
	@ docker compose -f $(DOCKER_DEV_COMPOSE_FILE) exec database psql --user postgres

clean: ## Remove all project images and volumes
	@ ${INFO} "Cleaning your local environment"
	@ ${INFO} "Note: All ephemeral volumes will be destroyed"
	@ docker compose -f $(DOCKER_DEV_COMPOSE_FILE) down --rmi all
	@ ${INFO} "Clean complete"

stop: ## Stop all project images and volumes
	@ ${INFO} "Stoping your local development server"
	@ docker-compose -f $(DOCKER_DEV_COMPOSE_FILE) down -v
	@ ${INFO} "Stop complete"

connect-to-container:build-image ## Connect to a container
	@ ${INFO} "Connecting to a container"
	@ docker compose -f $(DOCKER_DEV_COMPOSE_FILE) run --rm --service-ports api sh

test:build-image ## Run tests
	@ ${INFO} "Connecting to container"
	@ docker compose -f $(DOCKER_DEV_COMPOSE_FILE) exec api  python -m pytest
	@ ${INFO} "Tests complete"

# set default target
.DEFAULT_GOAL := help

# colors
YELLOW := $(shell tput -Txterm setaf 3)
NC := "\e[0m"

#shell Functions
INFO := @bash -c 'printf $(YELLOW); echo "===> $$1"; printf $(NC)' SOME_VALUE