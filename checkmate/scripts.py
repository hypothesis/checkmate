"""Entry-points for setup.py scripts.

To use run:

 * Install as a module (pip install -e)
 * initdb conf/development.ini
 * devdata conf/development.ini
"""
import os
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from pkg_resources import resource_filename
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


def update_remote_dev_data():
    """Get secrets and data stored in the devdata repo."""

    with TemporaryDirectory() as git_dir:
        subprocess.check_call(
            [
                "git",
                "clone",
                "git@github.com:hypothesis/devdata.git",
                git_dir,
                # Truncate the git history, we just want the files
                "--depth=1",
            ]
        )

        # Copy devdata env file into place.
        shutil.copyfile(
            os.path.join(git_dir, "checkmate", "devdata.env"),
            resource_filename("checkmate", "../.devdata.env"),
        )


def initialize_db():
    """Bootstrap the db in dev."""

    # Initialize the pyramid environment, which is enough to trigger the
    # initialisation code in `checkmate/db.py` to setup the DB for us.
    bootstrap(sys.argv[1])
