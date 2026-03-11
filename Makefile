SHELL := /bin/bash

WORKFLOW := ./scripts/workflow/acw.sh
STACK ?= all
ENV ?= testing
ACTION ?= ps
ARGS ?=
FORCE ?= 0

.PHONY: help doctor env-init build-images build-web sync-web stack dev-up dev-down prod-up prod-down

help:
	@$(WORKFLOW) help

doctor:
	@$(WORKFLOW) doctor

env-init:
	@$(WORKFLOW) env-init $(if $(filter 1 true yes,$(FORCE)),--force,)

build-images:
	@$(WORKFLOW) build-images $(STACK) $(ENV)

build-web:
	@$(WORKFLOW) build-web $(ENV)

sync-web:
	@$(WORKFLOW) sync-web $(ENV)

stack:
	@$(WORKFLOW) stack $(STACK) $(ENV) $(ACTION) $(ARGS)

dev-up:
	@$(WORKFLOW) dev-up $(STACK)

dev-down:
	@$(WORKFLOW) dev-down $(STACK)

prod-up:
	@$(WORKFLOW) prod-up $(STACK)

prod-down:
	@$(WORKFLOW) prod-down $(STACK)
