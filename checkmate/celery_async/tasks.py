"""Async tasks."""

from celery.utils.log import get_task_logger
from requests import RequestException

from checkmate.celery_async.celery import app
from checkmate.checker.url import CustomRules, URLHaus
from checkmate.exceptions import StageRetryableException

LOG = get_task_logger(__name__)


@app.task
def sync_blocklist():
    """Download the online version of the blocklist."""

    # pylint: disable=no-member
    # PyLint doesn't know about the `request_context` method that we add
    with app.request_context() as request:
        url = request.registry.settings["checkmate_blocklist_url"]
        if not url:
            LOG.warning("Not updating blocklist as no URL is present")
            return

        LOG.info("Updating blocklist from '%s'", url)

        with request.tm:
            try:
                raw_rules = CustomRules(request.db).load_simple_rule_url(url)
            except RequestException as err:
                LOG.exception("Could not update blocklist: %s", err)
                return

        LOG.info("Updated %s custom rules", len(raw_rules))


def pipeline_task(wrapped_function):
    """Mark a function as a standard checker pipeline task.

    This will automatically retry for the correct errors etc.
    """
    return app.task(
        autoretry_for=(StageRetryableException,),
        retry_kwargs={
            "max_retries": 3,
            # Time in seconds to delay the retry for.
            "countdown": 30,
        },
    )(wrapped_function)


@pipeline_task
def initialize_urlhaus():
    """Download the full URLHaus list to our DB."""

    # pylint: disable=no-member
    # PyLint doesn't know about the `request_context` method that we add
    with app.request_context() as request:
        LOG.info("Performing full URLHaus re-sync")

        with request.tm:
            synced = URLHaus(request.db).reinitialize_db()

        LOG.info("Reinitialized %s records", synced)


@pipeline_task
def sync_urlhaus():
    """Do a partial update of URLHaus rules."""

    # pylint: disable=no-member
    # PyLint doesn't know about the `request_context` method that we add
    with app.request_context() as request:
        LOG.info("Performing partial URLHaus update")

        with request.tm:
            synced = URLHaus(request.db).update_db()

        LOG.info("Synced %s records", synced)
