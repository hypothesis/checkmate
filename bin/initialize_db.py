"""Bootstrap the db in dev."""

import sys

from pyramid.paster import bootstrap

if __name__ == "__main__":
    CONFIG_FILE = sys.argv[1]
    # Initialize the pyramid environment, which is enough to trigger the

    # initialisation code in `checkmate/db.py` to setup the DB for us.
    bootstrap(CONFIG_FILE)
