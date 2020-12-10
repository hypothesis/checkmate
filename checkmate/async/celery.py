"""Celery app and configuration."""

import os
import sys
from contextlib import contextmanager
from logging import getLogger

import celery.signals
from celery import Celery
from kombu import Exchange, Queue
from pyramid.scripting import prepare

from checkmate.app import create_app
from checkmate.async.policy import RETRY_POLICY_QUICK

LOG = getLogger(__name__)


app = Celery("checkmate")
app.conf.update(
    # Without some kind of default here we can't even import the module
    # in the tests
    broker_url=os.environ.get(
        "CELERY_BROKER_URL", "amqp://guest:guest@localhost:5673//"
    ),
    # What options should we have when sending messages to the queue?
    broker_transport_options=RETRY_POLICY_QUICK,
    # Tell celery where our tasks are defined
    imports=("checkmate.async.tasks",),
    # Acknowledge tasks after the task has executed, rather than just before
    task_acks_late=True,
    # Don't store any results, we only use this for scheduling
    task_ignore_result=True,
    task_queues=[
        Queue(
            "celery",
            # We don't care if the messages are lost if the broker restarts
            durable=False,
            routing_key="celery",
            exchange=Exchange("celery", type="direct", durable=False),
        ),
    ],
    # Only accept one task at a time rather than pulling lots off the queue
    # ahead of time. This lets other workers have a go if we fail
    worker_prefetch_multiplier=1,
    worker_disable_rate_limits=True,
)


@celery.signals.worker_init.connect
def bootstrap_worker(sender, **_kwargs):  # pragma: no cover
    """Set up the celery worker with one-time initialisation."""

    # Put some common handy things around for tasks
    try:
        checkmate = create_app(celery_worker=True)

    # pylint: disable=broad-except
    except Exception as err:
        # If we don't bail out here ourselves, Celery just hides the error
        # and continues. This means `request_context` will not be available
        # when attempting to run tasks, which is impossible to debug.
        LOG.fatal("CELERY WORKER DID NOT START: Could not create app: %s", err)
        sys.exit(1)

    @contextmanager
    def request_context():
        with prepare(registry=checkmate.registry) as env:
            yield env["request"]

    sender.app.request_context = request_context
