"""Read CSV file of sites to add the the allow list and create a SQL file.

This script is intended to work with the CSV file at:

 * https://docs.google.com/spreadsheets/d/1g82noNwqN8Wzv3CplB_i4YP4iy9F_mhaSRz5xLUgfMY/edit#gid=0

It will:

 * Read that file (as a CSV)
 * Spot rows which don't have a result yet
 * Check if we can allow them and add them to the DB if so
 * Create an updated CSV file with the results of the run
 """

import csv
import os
from argparse import ArgumentParser
from datetime import date

import requests

from checkmate.models import Detection, Reason, Source

parser = ArgumentParser("A script for adding to the allow list")
parser.add_argument(
    "-i",
    "--input-csv",
    default="allow_list.csv",
    help="Input CSV file",
)
parser.add_argument(
    "-o", "--output_csv", default="allow_list.done.csv", help="Output CSV file"
)
parser.add_argument("-s", "--session", required=True, help="Admin session cookie value")
parser.add_argument("-r", "--route", required=True, help="Add rule end-point")


class AllowListCSV:
    """Read and write the allow list CSV in the expected formats."""

    EXPECTED_COLUMNS = [
        "id",
        "approved_url",
        "requested_url",
        "ticket",
        "result_date",
        "result",
    ]

    class Row(list):
        """A minimal wrapper around a row for convenience."""

        @property
        def approved_url(self):
            return self[1]

        @property
        def result(self):
            return self[-1]

        @result.setter
        def result(self, value):
            today = date.today().isoformat()
            self[-2] = today
            self[-1] = value

    @classmethod
    def read(cls, filename):
        with open(filename, encoding="utf8") as handle:
            reader = csv.reader(handle)

            # What are you on about Pylint?
            header = next(reader)  # pylint: disable=stop-iteration-return

            if header != cls.EXPECTED_COLUMNS:
                raise ValueError(
                    f"Expected headers: {cls.EXPECTED_COLUMNS} not {header}"
                )

            for row in reader:
                yield cls.Row(row)

    @classmethod
    def write(cls, handle, rows):
        writer = csv.writer(handle)
        writer.writerow(cls.EXPECTED_COLUMNS)
        writer.writerows(rows)


ALLOW_LIST_DETECTION = Detection(Reason.NOT_ALLOWED, Source.ALLOW_LIST)


class Checkmate:
    def __init__(self, route, session):
        self.route = route
        self.session = session

    def allow_url(self, url):
        response = requests.post(
            self.route,
            headers={"Cookie": f"session={self.session}"},
            json={"data": {"type": "AllowRule", "attributes": {"url": url}}},
            timeout=(10, 10),
        )

        if response.ok:
            attributes = response.json()["data"]["attributes"]
            hex_hash = attributes["hash"]
            rule = attributes["rule"]

            return True, f"Allowed as {rule} with hash {hex_hash}"

        if response.status_code == 409:
            return False, response.json()["errors"][0]["detail"]

        if response.status_code == 404:
            # If we ever sort out the permissiosns / principals stuff we'll get
            # a nice 404 / 401 to be able to tell the difference
            raise ConnectionError(
                "Either your session has expired, or the route you have "
                "provided is not correct"
            )

        raise ConnectionError(
            f"Unexpected error when connecting to checkmate: {response}: {response.content}"
        )


def main():
    args = parser.parse_args()

    if not os.path.isfile(args.input_csv):
        raise EnvironmentError(f"Could not find expected file '{args.input_csv}'")

    checkmate = Checkmate(route=args.route, session=args.session)
    rows = list(AllowListCSV.read(args.input_csv))

    changed = 0

    for row in rows:
        # This has already been dealt with
        if row.result:
            continue

        changed += 1
        rule_accepted, row.result = checkmate.allow_url(row.approved_url)

        if rule_accepted:
            print(f"Added row: {row}")
        else:
            print(f"Failed on row: {row}")

    if not changed:
        print("No rows were altered. No CSV created")
        return

    # Create the output CSV file
    with open(args.output_csv, "w", encoding="utf8") as handle:
        AllowListCSV.write(handle, rows=rows)

    print(f"Created CSV file: {args.output_csv}")


if __name__ == "__main__":
    main()
