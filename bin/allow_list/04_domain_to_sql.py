"""Convert a list of domains to hashed SQL.

You MUST import the real blocklist from the S3 bucket before running this.
"""

from bin.allow_list.file_tools import load_json
from checkmate.checker.url import CustomRules, URLHaus
from checkmate.db import SESSION, create_engine
from checkmate.url import hash_for_rule


class DomainHash:
    """An object for checking URLs against our blocklist and hashing them."""

    def __init__(self):
        engine = create_engine(
            database_url="postgresql://postgres@localhost:5434/postgres"
        )
        session = SESSION(bind=engine)

        self.url_haus = URLHaus(session)
        self.blocklist = CustomRules(session)

    def hash_domains(self, sourced_domains):
        for pos, (domain, source) in enumerate(sourced_domains):
            expanded_url, url_hash = self._hash_domain(domain)

            if expanded_url is None:
                continue

            if pos % 1000 == 0:
                print(pos, "/", len(sourced_domains))

            yield expanded_url, url_hash, source

    def _hash_domain(self, domain):
        raw_url = f"http://{domain}/"
        expanded_url, url_hash = hash_for_rule(raw_url)

        url_haus_reasons = tuple(self.url_haus.check_url([url_hash]))
        if url_haus_reasons:
            print("BLOCKED (URLHaus!)", domain, url_haus_reasons)
            return None, None

        our_reasons = tuple(self.blocklist.check_url([url_hash]))
        if our_reasons:
            print("BLOCKED (Us!)", domain, our_reasons)
            return None, None

        return expanded_url, url_hash


if __name__ == "__main__":
    sourced_domains = load_json("process/04_domains_reduced.json")

    with open("process/05_domains.sql", "w") as handle:
        handle.write("DELETE FROM allow_rule;\n")
        handle.write("INSERT INTO allow_rule (rule, hash, tags)\nVALUES\n")

        first = True
        for url, hash, source in DomainHash().hash_domains(sourced_domains):
            if first:
                first = False
            else:
                handle.write(",\n")

            handle.write(f"\t('{url}', '{hash}', '{{\"auto\", \"{source}\"}}')")

        handle.write(";\n")
