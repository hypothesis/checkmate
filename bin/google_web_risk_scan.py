"""
Instructions:

 * Get a set of service account credentials here: https://console.cloud.google.com/apis/credentials?folder=&organizationId=&project=checkmate-302812
 * This should provide you with a JSON credentials file
 * Call this "web_risk_credentials.json" and save it in "checkmate/bin"
 * Hack `requirements/dev.txt` and add `google-cloud-webrisk`
 * `tox -qe dev --run-command "python bin/google_web_risk_scan.py"`

"""

import json
import os
import sys
from contextlib import contextmanager

# pylint: disable=invalid-name,too-many-try-statements,redefined-outer-name

try:
    from google.api_core.exceptions import ClientError, PermissionDenied
    from google.cloud.webrisk_v1.services.web_risk_service import WebRiskServiceClient
    from google.cloud.webrisk_v1.types.webrisk import SearchUrisRequest, ThreatType
    from google.oauth2 import service_account
except ImportError as err:
    print("You must install 'google-cloud-webrisk'")
    sys.exit(1)

from pyramid.paster import bootstrap

from checkmate.models import AllowRule


class WebRiskAPI:
    THREAT_TYPES = [
        ThreatType.MALWARE,
        ThreatType.SOCIAL_ENGINEERING,
        # ThreatType.UNWANTED_SOFTWARE
    ]

    def __init__(self, service_account_info):
        self._credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=[]
        )

        self._service = WebRiskServiceClient(credentials=self._credentials)

    def check_url(self, url):
        # https://googleapis.dev/python/webrisk/latest/webrisk_v1/services.html

        # This isn't really documented from what I can see, but this appears
        # to be how these object work?
        request = SearchUrisRequest(uri=url, threat_types=self.THREAT_TYPES)

        # It looks in the docs like you can pass the above arguments straight
        # to search_uris(), but it seems to fall over it's own validation if
        # you do that, and complains the passed enum is not an enum
        try:
            response = self._service.search_uris(request=request)

        except PermissionDenied as err:
            print("Oh no, permission denied!", err)
            raise
        except ClientError as err:
            print("On no!", err)
            raise

        # response.threat.expire_time
        return response.threat.threat_types


@contextmanager
def request_context():
    with bootstrap("conf/development.ini") as env:
        with env["request"].tm:
            yield env["request"]


if __name__ == "__main__":
    with open("bin/web_risk_credentials.json") as handle:
        credentials = json.load(handle)
        web_risk_api = WebRiskAPI(credentials)

    start_from = -1
    rules_per_run = 50000
    dry_run = False
    completed = 0

    # Check to see if we need to pick up where we left off
    if os.path.isfile("progress.ndjson"):
        threats = 0

        with open("progress.ndjson") as progress:
            last_line = None
            for line in progress:
                if line.startswith('["NOK",'):
                    threats += 1

                completed += 1
                last_line = line

            if last_line:
                last_line = json.loads(last_line)
                start_from = last_line[1]
                print(f"Restarting from {last_line}")

            print(f"{threats} threat(s) found so far")

    # Main loop
    with open("progress.ndjson", mode="a") as progress:
        with request_context() as request:
            count = 0
            total = request.db.query(AllowRule).count()

            query = (
                request.db.query(AllowRule.id, AllowRule.rule)
                .filter(AllowRule.id > start_from)
                .order_by(AllowRule.id)
            )

            for count, (rule_id, rule) in enumerate(query.limit(rules_per_run)):
                url = f"https://{rule}"

                threats = [] if dry_run else web_risk_api.check_url(url)
                if threats:
                    print(f"Threats found for {url}\n\t{threats}")

                # Keep writing lines to the progress file. The last line is
                # used to start from where we left off when the script is
                # run again
                progress.write(
                    json.dumps(
                        [
                            "NOK" if threats else "OK",
                            rule_id,
                            rule,
                            [threat.name for threat in threats],
                        ]
                    )
                    + "\n"
                )

                completed += 1

                if not count % 100:
                    # Make sure the file is updated as we go
                    progress.flush()

                    print(
                        f"Complete {completed}/{total} {100 * completed / total}% (this run: {count})"
                    )

            print(f"Checked {count + 1} rules. Done.")
