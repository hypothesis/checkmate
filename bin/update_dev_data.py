"""Setup some basic local data to test with."""

import os
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import importlib_resources
from pyramid.paster import bootstrap

from checkmate.checker.url.custom_rules import CustomRules
from checkmate.models import Reason


def update_remote_dev_data():
    """Get secrets and data stored in the devdata repo."""

    with TemporaryDirectory() as git_dir:
        subprocess.check_call(
            [
                "git",
                "clone",
                "https://github.com/hypothesis/devdata.git",
                git_dir,
                # Truncate the git history, we just want the files
                "--depth=1",
            ]
        )

        # Copy devdata env file into place.
        shutil.copyfile(
            os.path.join(git_dir, "checkmate", "devdata.env"),
            importlib_resources.files("checkmate") / "../.devdata.env",
        )


def update_dev_data():
    """Create some usable data to run against in dev."""

    raw_rules = {
        "example.org": Reason.PUBLISHER_BLOCKED,
        "example.net": Reason.MEDIA_VIDEO,
        "bad.example.com": Reason.MALICIOUS,
    }
    CustomRules(request.db).load_simple_rules(raw_rules)
    print(f"Loaded {len(raw_rules)} custom rules")


if __name__ == "__main__":
    update_remote_dev_data()

    config_file = sys.argv[1]
    with bootstrap(config_file) as env:
        request = env["request"]

        with request.tm:
            update_dev_data()
