FROM python:3.11.7-alpine3.16

RUN apk add --no-cache nginx supervisor

RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

COPY requirements/prod.txt ./

RUN apk add --no-cache --virtual \
    build-deps \
    build-base \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r prod.txt \
  && apk del build-deps

COPY . .

EXPOSE 9099

USER hypothesis

CMD /usr/bin/supervisord -c /var/lib/hypothesis/conf/supervisord.conf
