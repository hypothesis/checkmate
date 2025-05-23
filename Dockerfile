FROM python:3.11.11-alpine3.19
LABEL maintainer="Hypothes.is Project and contributors"

# Install nginx & supervisor
RUN apk add --no-cache nginx gettext supervisor libpq git

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Copy minimal data to allow installation of python dependencies.
COPY requirements/requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk add --no-cache --virtual \
    build-deps \
    build-base \
    postgresql-dev \
    libffi-dev \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

COPY . .

ENV PYTHONPATH /var/lib/hypothesis:$PYTHONPATH

USER hypothesis

CMD /usr/bin/supervisord -c /var/lib/hypothesis/conf/supervisord.conf
