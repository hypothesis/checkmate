"""Entry-points for setup.py scripts.

To use run:

 * Install as a module (pip install -e)
 * initdb conf/development.ini
 * devdata conf/development.ini
"""

import sys

from pyramid.paster import bootstrap

from checkmate.checker.url.custom_rules import CustomRules
from checkmate.models import Reason


def update_dev_data():
    """Create some usable data to run against in dev."""
    config_file = sys.argv[1]

    with bootstrap(config_file) as env:
        request = env["request"]

        with request.tm:
            raw_rules = {
                "example.org": Reason.PUBLISHER_BLOCKED,
                "example.net": Reason.MEDIA_VIDEO,
                "bad.example.com": Reason.MALICIOUS,
            }
            CustomRules(request.db).load_simple_rules(raw_rules)
            print(f"Loaded {len(raw_rules)} custom rules")


def initialize_db():
    """Bootstrap the db in dev."""

    # Initialize the pyramid environment, which is enough to trigger the
    # initialisation code in `checkmate/db.py` to setup the DB for us.
    bootstrap(sys.argv[1])
