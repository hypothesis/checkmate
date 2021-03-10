import json
from contextlib import contextmanager
from datetime import datetime

from google.api_core.exceptions import ClientError, PermissionDenied
# pip install google-cloud-webrisk
from google.cloud.webrisk_v1.services.web_risk_service import WebRiskServiceClient
from google.cloud.webrisk_v1.types.webrisk import SearchUrisRequest, ThreatType
from google.oauth2 import service_account


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

        return response.threat.threat_types, response.threat.expire_time


@contextmanager
def timeit():
    start = datetime.utcnow()

    yield

    diff = datetime.utcnow() - start
    millis = diff.seconds * 1000 + (diff.microseconds / 1000)
    print(f"{millis}ms")


if __name__ == "__main__":
    with open("Checkmate-b0fd5a96e470.json") as handle:
        credentials = json.load(handle)

    url = "http://example.com"
    url = "http://via3.hypothes.is"

    malicious = [
        # "sdrjk6ydtckjmndtntre5.web.app",
        # "ydf774766fygrbehf.web.app",
        # "t6gr3efetf6tg4y.web.app",
        "canadacigarsupplies.com",
        "medyanef.com",
        # "webmail.belgran.by",
        # "executivewrite.com",
        # "nmztd.ru",
        # "cp.regruhosting.ru",
        # "manikmeyah.net"
    ]

    with timeit():
        web_risk_api = WebRiskAPI(credentials)

    for url in malicious:
        print(f"CHECKING {url}")

        with timeit():
            wat = web_risk_api.check_url(url)
            print("WAT", wat, type(wat))
