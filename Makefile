.PHONY: *
.DEFAULT_GOAL := help

SHELL := /bin/bash

WORK ?= $(HOME)/kart64-work
BUILD_DIR := $(WORK)/SpaghettiKart/build/emscripten
PORT ?= 8099
PACK_ARGS ?= --scale 0.5 --kart-scale 0.375

##@ Setup

deps: ## Install the test dependencies and Playwright's Chromium
	npm ci --prefix tests --no-audit --no-fund
	cd tests && npx playwright install chromium

##@ Development

build: ## Build the engine and page into WORK (default ~/kart64-work)
	WORK="$(WORK)" scripts/build.sh

start: _require_build ## Serve the local build at http://localhost:8099/
	python3 scripts/serve.py "$(BUILD_DIR)" $(PORT)

start/plain: _require_build ## Serve without isolation headers, as GitHub Pages does
	python3 scripts/serve.py "$(BUILD_DIR)" $(PORT) --plain

patches: ## Regenerate patches/ from the patched tree in WORK
	scripts/regen-patches.sh "$(WORK)/SpaghettiKart"

##@ Testing/Linting

can-release: lint security test ## Run the ROM-free checks expected before release

lint: ## Check script syntax and that no ROM-derived files are tracked
	@for f in scripts/*.sh; do bash -n "$$f"; done
	@python3 -c 'import ast, sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]' scripts/*.py media/mario-raceway/generate.py
	@for f in tests/*.mjs web/coi-sw.js; do node --check "$$f"; done
	@if git ls-files | grep -iE '\.(z64|v64|n64|o2r)$$|(^|/)baserom'; then \
		printf '\033[31mROM-derived files are tracked; remove them from Git.\033[0m\n' >&2; exit 1; \
	fi
	@echo "Lint: PASS"

security: ## Audit the test dependencies
	npm audit --prefix tests

test: ## Run the startup gate test (no build or ROM needed)
	cd tests && node gate-test.mjs

test/layout: _require_build ## Run the layout test against the local build
	cd tests && node layout-test.mjs "$(BUILD_DIR)"

test/rom: _require_build _require_rom ## Run ROM extraction checks (ROM=path/to/mk64.z64)
	cd tests && ROM_PATH="$(ROM)" node rom-test.mjs "$(BUILD_DIR)"

test/race: _require_build _require_rom ## Run full races with touch input (ROM=path/to/mk64.z64)
	cd tests && ROM_PATH="$(ROM)" node race-test.mjs "$(BUILD_DIR)"

##@ Build/Deploy

dist: _require_build ## Assemble the deployable site in dist/
	scripts/make-dist.sh "$(BUILD_DIR)" dist

deploy: ## Build and publish to GitHub Pages
	WORK="$(WORK)" scripts/publish.sh

deploy/no-build: _require_build ## Publish the last build to GitHub Pages with the current page
	WORK="$(WORK)" scripts/publish.sh --no-build

clean: ## Remove dist/ and the test dependencies
	rm -rf dist tests/node_modules

##@ Media

pack/trim: _require_PACK _require_OUT ## Make a lighter texture pack (PACK=in.o2r OUT=out.o2r PACK_ARGS="...")
	uv run --no-project --with pillow scripts/trim-pack.py "$(PACK)" "$(OUT)" $(PACK_ARGS)

media/screenshots: ## Regenerate the Mario Raceway showcase screenshots
	uv run --no-project media/mario-raceway/generate.py

_require_build:
	@[ -f "$(BUILD_DIR)/Spaghettify.js" ] || { printf '\033[31mNo build in %s. Run make build first.\033[0m\n' "$(BUILD_DIR)" >&2; exit 1; }

_require_rom:
	@[ -n "$(ROM)" ] && [ -f "$(ROM)" ] || { printf '\033[31mSet ROM to your own US ROM, e.g. make test/rom ROM=~/roms/mk64.z64\033[0m\n' >&2; exit 1; }

_require_%:
	@[ -n "$($*)" ] || { printf '\033[31mSet %s, e.g. make pack/trim PACK=in.o2r OUT=out.o2r\033[0m\n' "$*" >&2; exit 1; }

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_%\/-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
