#!/bin/sh

# No dependencies
tox -e dev --run-command "pip-compile requirements/requirements.in"
tox -e format --run-command "pip-compile requirements/format.in"

# Depends on requirements.txt
tox -e dev --run-command "pip-compile requirements/dev.in"
tox -e tests --run-command "pip-compile requirements/tests.in"

# Depends on requirements.txt and tests.txt
tox -e lint --run-command "pip-compile requirements/lint.in"
