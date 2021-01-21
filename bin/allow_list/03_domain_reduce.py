"""Remove redundant or overly specific domains."""

from collections import Counter

from bin.allow_list.file_tools import load_json, load_text, save_json
from bin.allow_list.winnow import winnow
from checkmate.url.domain import Domain


class SourcedDomain(Domain):
    source = None

    def __new__(cls, domain, source, **kwargs):
        return super().__new__(cls, cls._normalize(domain), **kwargs)

    def __init__(self, _domain, source):
        self.source = source
        super().__init__()


class DomainData:
    @classmethod
    def load(cls):
        domains = cls._load_sourced_domains()

        return cls._split_by_ip(domains)

    @classmethod
    def _load_sourced_domains(cls):
        domains = cls._single_source("process/02_domains.txt", "h")

        # Some hand curated simplications of the domains from H
        domains |= cls._single_source("data/domains_hand_picked.txt", "h")

        # Some extracted by the experimental suffix identifier
        domains |= cls._single_source("process/03_auto_suffixes.txt", "h")

        # A list of popular sites
        top_1000 = cls._single_source("data/domains_top_1000.txt", "top_1000")

        # A list of ads and trackers we've seen break pages if not enabled
        ads_and_others = set(
            SourcedDomain(domain, source)
            for domain, source in load_json("data/domains_hand_picked.json")
        )

        # Make sure "H" as the source takes precedence
        top_1000 -= domains
        ads_and_others -= domains

        # Then merge them in
        domains |= top_1000 | ads_and_others

        return domains

    @classmethod
    def _single_source(cls, text_file, source):
        return set(SourcedDomain(domain, source) for domain in load_text(text_file))

    @classmethod
    def _split_by_ip(cls, domains):
        ips = set()
        domain_names = set()

        # Separate out the IPs before we process anything
        for domain in domains:
            if domain.is_ip_v4:
                ips.add(domain)
            else:
                domain_names.add(domain)

        return domain_names, ips


class DomainReducer:
    ISO_639_1_LANGUAGE_CODES = set(load_json("data/iso_639_1_language_codes.json"))

    @classmethod
    def reduce(cls, domain_set):
        # Remove domains which are covered by things in the list
        print(f"Start with {len(domain_set)}")

        winnow(domain_set)
        prefixes = set(cls._common_prefixes(domain_set))

        last_size = 0
        while last_size != len(domain_set):
            last_size = len(domain_set)

            cls._remove_prefixes(domain_set, prefixes)

            winnow(domain_set)

            print(f"\tSet reduced to: {len(domain_set)}")

        print("\tNo further reduction in size")

    @classmethod
    def _common_prefixes(cls, domains, min_count=15):
        prefixes = Counter()

        for domain in domains:
            sub_domains, _root_domain = domain.split_domain()
            if not sub_domains:
                continue

            prefixes[sub_domains[0]] += 1

        prefixes.pop("via", None)

        # Also include common language prefixes
        yield from cls.ISO_639_1_LANGUAGE_CODES

        for prefix, count in prefixes.most_common():
            if count < min_count:
                return

            yield prefix

    @classmethod
    def _remove_prefixes(cls, domain_set, prefixes):
        removed = set()
        added = set()

        for domain in domain_set:
            sub_domains, root_domain = domain.split_domain()
            if not sub_domains:
                continue

            if sub_domains[0] in prefixes:
                stripped_domain = ".".join(sub_domains[1:] + [root_domain])

                added.add(SourcedDomain(stripped_domain, domain.source))
                removed.add(domain)

        domain_set -= removed
        domain_set |= added


if __name__ == "__main__":
    domain_names, ips = DomainData.load()

    DomainReducer.reduce(domain_names)

    data = [[domain, domain.source] for domain in sorted(domain_names | ips)]

    save_json("process/04_domains_reduced.json", data)
