"""Read CSV file of sites to add the the allow list and create a SQL file.

This script is intended to work with the CSV file at:

 * https://docs.google.com/spreadsheets/d/1g82noNwqN8Wzv3CplB_i4YP4iy9F_mhaSRz5xLUgfMY/edit#gid=0

It will:

 * Read that file (as a CSV)
 * Spot rows which don't have a result yet
 * Check if we can allow them
 * Create an SQL file to add to the running server
 * Create an updated CSV file with the results of the run
 """

import csv
import json
import os
from argparse import ArgumentParser
from datetime import date

from pkg_resources import resource_filename
from pyramid.paster import bootstrap

from checkmate.models import Detection, Reason, Source
from checkmate.services import URLCheckerService
from checkmate.url import hash_for_rule

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
parser.add_argument("-s", "--sql", default="allow_list.sql", help="Output SQL file")


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
        with open(filename) as handle:
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


def check_rows(rows, checker):
    """Check each row for detections and hash if none are found.

    This will skip existing rows with results from previous runs.
    """

    for row in rows:
        # This has already been dealt with
        if row.result:
            continue

        # Don't fail fast, so we get all of the detections
        reasons = list(checker.check_url(row.approved_url, fail_fast=False))

        try:
            # We expect a detection from not being on the allow list, so we'll
            # remove it, which will trigger a ValueError if it wasn't there
            reasons.remove(ALLOW_LIST_DETECTION)
        except ValueError:
            row.result = "Already allowed"
            continue

        # After the expected allow list detection is gone, any remaining
        # reasons are because the URL is blocked
        if reasons:
            row.result = f"Detections found: {reasons}"
        else:
            rule, hex_hash = hash_for_rule(row.approved_url)
            row.result = f"Added to allow list as: '{rule}'"

            yield rule, hex_hash


def create_sql(handle, rule_hashes, tags):
    """Write out the hashes into an SQL file for importing into Postgres."""

    handle.write("INSERT INTO allow_rule (rule, hash, tags)\nVALUES\n")

    tags = json.dumps(list(tags)).strip("[]")
    tags = f"{{{tags}}}"

    first = True
    for rule, hex_hash in rule_hashes:
        if first:
            first = False
        else:
            handle.write(",\n")

        handle.write(f"\t('{rule}', '{hex_hash}', '{tags}')")

    handle.write(";\n")


def main():
    args = parser.parse_args()

    if not os.path.isfile(args.input_csv):
        raise EnvironmentError(f"Could not find expected file '{args.input_csv}'")

    # Check all the rows

    rows = list(AllowListCSV.read(args.input_csv))

    config_file = resource_filename("checkmate", "../conf/development.ini")
    with bootstrap(config_file) as env:
        request = env["request"]
        checker = request.find_service(URLCheckerService)

        with request.tm:
            rule_hashes = list(check_rows(rows, checker))

    # Create the output files

    with open(args.sql, "w") as handle:
        create_sql(handle, rule_hashes=rule_hashes, tags=["manual"])

    with open(args.output_csv, "w") as handle:
        AllowListCSV.write(handle, rows=rows)

    print(f"Created SQL file: {args.sql}")
    print(f"Creating CSV file: {args.output_csv}")


if __name__ == "__main__":
    main()
