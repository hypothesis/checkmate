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
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
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
	@docker compose $(args)

.PHONY: db
db: args?=upgrade head
db: python
	@tox -qe dev --run-command 'python3 -m checkmate.scripts.init_db --create --stamp'
	@tox -qe dev  --run-command 'alembic -c conf/alembic.ini $(args)'

.PHONY: shell
shell: python
	@tox -qe dev --run-command 'pshell conf/development.ini'

.PHONY: sql
sql: python
	@docker compose exec postgres psql --pset expanded=auto -U postgres

.PHONY: devdata
devdata: python
	@tox -qe dev --run-command 'python3 -m checkmate.scripts.init_db --create --stamp'
	@tox -qe dev --run-command 'python bin/update_dev_data.py conf/development.ini'

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

.PHONY: coverage
coverage: python
	@tox -qe coverage

.PHONY: functests
functests: python
	@tox -qe functests

# Tell make how to compile requirements/*.txt files.
#
# `touch` is used to pre-create an empty requirements/%.txt file if none
# exists, otherwise tox crashes.
#
# $(subst) is used because in the special case of making requirements.txt we
# actually need to touch dev.txt not requirements.txt and we need to run
# `tox -e dev ...` not `tox -e requirements ...`
#
# $(basename $(notdir $@))) gets just the environment name from the
# requirements/%.txt filename, for example requirements/foo.txt -> foo.
requirements/%.txt: requirements/%.in
	@touch -a $(subst requirements.txt,dev.txt,$@)
	@tox -qe $(subst requirements,dev,$(basename $(notdir $@))) --run-command 'pip --quiet --disable-pip-version-check install pip-tools'
	@tox -qe $(subst requirements,dev,$(basename $(notdir $@))) --run-command 'pip-compile --allow-unsafe --quiet $(args) $<'

# Inform make of the dependencies between our requirements files so that it
# knows what order to re-compile them in and knows to re-compile a file if a
# file that it depends on has been changed.
requirements/dev.txt: requirements/requirements.txt
requirements/tests.txt: requirements/requirements.txt
requirements/functests.txt: requirements/requirements.txt
requirements/lint.txt: requirements/tests.txt requirements/functests.txt

# Add a requirements target so you can just run `make requirements` to
# re-compile *all* the requirements files at once.
#
# This needs to be able to re-create requirements/*.txt files that don't exist
# yet or that have been deleted so it can't just depend on all the
# requirements/*.txt files that exist on disk $(wildcard requirements/*.txt).
#
# Instead we generate the list of requirements/*.txt files by getting all the
# requirements/*.in files from disk ($(wildcard requirements/*.in)) and replace
# the .in's with .txt's.
.PHONY: requirements requirements/
requirements requirements/: $(foreach file,$(wildcard requirements/*.in),$(basename $(file)).txt)

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
