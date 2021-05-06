.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo "make supervisor        Launch a supervisorctl shell for managing the processes "
	@echo '                       that `make dev` starts, type `help` for docs'
	@echo 'make services          Run the services that `make dev` requires'
	@echo 'make db                Upgrade the DB schema to the latest version'
	@echo "make shell             Launch a Python shell in the dev environment"
	@echo "make sql               Connect to the dev database with a psql shell"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests and produce a coverage report"
	@echo "make functests         Run the functional tests"
	@echo "make sure              Make sure that the formatter, linter, tests, etc all pass"
	@echo "make docker            Make the app's Docker image"
	@echo "make allow-list        Create an SQL file for adding sites to the allow list"

.PHONY: dev
dev: python
	@tox -qe dev

.PHONY: supervisor
supervisor: python
	@tox -qe dev --run-command 'supervisorctl -c conf/supervisord-dev.conf $(command)'

.PHONY: services
services: args?=up -d
services: python
	@tox -qe dockercompose -- $(args)

.PHONY: db
db: args?=upgrade head
db: python
	@tox -qqe dev --run-command 'initdb conf/development.ini'  # See setup.py for what initdb is.
	@tox -qe dev  --run-command 'alembic -c conf/alembic.ini $(args)'

.PHONY: shell
shell: python
	@tox -qe dev --run-command 'pshell conf/development.ini'

.PHONY: sql
sql: python
	@tox -qe dockercompose -- exec postgres psql --pset expanded=auto -U postgres

.PHONY: devdata
devdata: python
	# See setup.py for what devdata and devdata-remote are.
	@tox -qe dev --run-command 'devdata-remote'
	@tox -qe dev --run-command 'devdata conf/development.ini'

.PHONY: lint
lint: python
	@tox -qe lint

.PHONY: format
format: python
	@tox -qe format

.PHONY: checkformatting
checkformatting: python
	@tox -qe checkformatting

.PHONY: test
test: python
	@tox -q

.PHONY: functests
functests: python
	@tox -qe functests

.PHONY: sure
sure: checkformatting lint test functests

.PHONY: docker
docker:
	@git archive --format=tar HEAD | docker build -t hypothesis/checkmate:$(DOCKER_TAG) -

.PHONY: run-docker
run-docker:
	@docker run \
	    -it --rm \
	    -e "NEW_RELIC_LICENSE_KEY=$(NEW_RELIC_LICENSE_KEY)" \
	    -e "NEW_RELIC_ENVIRONMENT=dev" \
	    -e "NEW_RELIC_APP_NAME=checkmate (dev)" \
	    -e "CHECKMATE_BLOCKLIST_URL=https://hypothesis-via.s3-us-west-1.amazonaws.com/via-blocklist.txt" \
	    -p 9099:9099 \
	    --name checkmate hypothesis/checkmate:$(DOCKER_TAG)

.PHONY: web
web: python
	@tox -qe dev --run-command 'gunicorn -c conf/gunicorn/dev.conf.py --paste conf/development.ini'

.PHONY: python
python:
	@./bin/install-python


DOCKER_TAG = dev
