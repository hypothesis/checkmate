#!/usr/bin/env python3
"""A script for syncing the filebased blocklist to the DB.

We shouldn't need this for long
"""

import sys
from logging import getLogger

from pyramid.scripting import prepare

from checkmate.app import create_app
from checkmate.checker.url.blocklist import Blocklist
from checkmate.checker.url.custom_rules import CustomRules

LOG = getLogger(__name__)


def sync_blocklist(request):
    """Sync the file based blocklist to the DB."""

    if not hasattr(request, "db"):
        LOG.warning("Skipping update as DATABASE_URL is not configured")
        sys.exit()

    blocklist = Blocklist(request.registry.settings["checkmate_blocklist_path"])
    rules = CustomRules(request.db)

    with request.tm:
        rules.update_from_blocklist_rules(blocklist.raw_rules)

    LOG.info("Synced %s to the DB", len(blocklist.raw_rules))


if __name__ == "__main__":
    app = create_app()

    with prepare(registry=app.registry) as env:
        sync_blocklist(request=env["request"])
