#!/bin/sh

# Get around the year zero problem of not being able to create requirements
# files because there are no requirements files for the tox envs.
touch requirements/requirements.txt
touch requirements/dev.txt
touch requirements/format.txt
touch requirements/tests.txt
touch requirements/lint.txt
touch requirements/dockercompose.txt

# No dependencies
tox -e dev --run-command "pip-compile requirements/requirements.in"
tox -e format --run-command "pip-compile requirements/format.in"
tox -e dockercompose --run-command "pip-compile requirements/dockercompose.in"

# Depends on requirements.txt
tox -e dev --run-command "pip-compile requirements/dev.in"
tox -e tests --run-command "pip-compile requirements/tests.in"

# Depends on requirements.txt and tests.txt
tox -e lint --run-command "pip-compile requirements/lint.in"
