"""Async tasks."""

from celery.utils.log import get_task_logger
from requests import RequestException

from checkmate.async.celery import app
from checkmate.checker.url.custom_rules import CustomRules

LOG = get_task_logger(__name__)


@app.task
def sync_blocklist():
    """Download the online version of the blocklist."""

    # pylint: disable=no-member
    # Pylint doesn't know about the `request_context` method that we add
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
                LOG.error("Could not update blocklist with error: %s", err)
                return

        LOG.info("Updated %s custom rules", len(raw_rules))
