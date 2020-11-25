"""Entry-points for setup.py scripts.

To use run:

 * Install as a module (pip install -e)
 * initdb conf/development.ini
 * devdata conf/development.ini
"""

import sys

from pyramid.paster import bootstrap


def update_dev_data():
    """Create some usable data to run against in dev."""
    config_file = sys.argv[1]

    with bootstrap(config_file) as env:
        _request = env["request"]

        # Go forth and add data...
        print("NOT IMPLEMENTED YET")

        # For checkmate this is probably a case of pulling down a few lists
        # from the internet or something


def initialize_db():
    """Bootstrap the db in dev."""

    # Initialise the pyramid environment, which is enough to trigger the
    # initialisation code in `checkmate/db.py` to setup the DB for us.
    bootstrap(sys.argv[1])
