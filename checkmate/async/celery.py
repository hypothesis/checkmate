"""Celery app and configuration."""

import os

from celery import Celery
from kombu import Exchange, Queue

from checkmate.async.policy import RETRY_POLICY_QUICK

app = Celery("checkmate")
app.conf.update(
    broker_url=os.environ["CELERY_BROKER_URL"],
    # What options should we have when sending messages to the queue?
    broker_transport_options=RETRY_POLICY_QUICK,
    # Tell celery where our tasks are defined
    imports=("checkmate.async.tasks",),
    # Acknowledge tasks after the task has executed, rather than just before
    task_acks_late=True,
    # Don't store any results, we only use this for scheduling
    task_ignore_result=True,
    task_default_queue="checkmate",
    task_queues=[
        Queue(
            "checkmate",
            # We don't care if the messages are lost if the broker restarts
            durable=False,
            routing_key="checkmate",
            exchange=Exchange("checkmate", type="direct", durable=False),
        ),
    ],
    # Only accept one task at a time rather than pulling lots off the queue
    # ahead of time. This lets other workers have a go if we fail
    worker_prefetch_multiplier=1,
    worker_disable_rate_limits=True,
)
