"""Async tasks."""

from celery.utils.log import get_task_logger

from checkmate.async.celery import app
from checkmate.checker.url.blocklist import Blocklist

LOG = get_task_logger(__name__)


@app.task
def sync_blocklist():
    """Download the online version of the blocklist."""

    local_path = app.checkmate.registry.settings["checkmate_blocklist_path"]
    url = app.checkmate.registry.settings["checkmate_blocklist_url"]

    LOG.info(f"Updating blocklist from '{url}' >> '{local_path}'")

    Blocklist(local_path).sync(url)
