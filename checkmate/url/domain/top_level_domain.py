"""Tools for checking top level domains."""

import re

from checkmate.url.domain._data import load_data
from checkmate.url.domain._domain_core import DomainCore


class TopLevelDomain:
    """Tools for checking top level domains.

    The top level domain is the last label of a domain, which must also
    be a recognised ICANN value. Therefore many valid domain names will have
    a last label, which is not a top level domain, by this definition:

        www.google.com -> com
        my_home_server.local -> None
    """

    TLDS = set()
    VALID_TLD_SUFFIX = None

    @classmethod
    def is_tld(cls, suffix):
        """Find out if the given suffix is a recognised top level domain.

        :param suffix: Suffix to test
        :rtype: bool
        """

        return suffix in cls.TLDS

    @classmethod
    def has_tld(cls, domain):
        """Find out if the suffix has a valid top level domain.

        :param domain: Domain object to test
        :rtype: bool
        """

        if not domain:
            return False

        return bool(cls.VALID_TLD_SUFFIX.search(domain))

    @classmethod
    def get_tld(cls, domain):
        """Get the public suffix from a domain.

        :param domain: Domain object to retrieve suffix from
        :return: The top level domain or None
        """

        if cls.has_tld(domain):
            if not isinstance(domain, DomainCore):
                domain = DomainCore(domain)

            return domain.suffix(depth=1)

        return None

    @classmethod
    def _load(cls):
        cls.TLDS = set(
            line.lower()
            for line in load_data("resource/data/valid_top_level_domains.txt")
        )
        cls.VALID_TLD_SUFFIX = re.compile(fr"\.(?:{'|'.join(cls.TLDS)})$")


TopLevelDomain._load()  # pylint: disable=protected-access
