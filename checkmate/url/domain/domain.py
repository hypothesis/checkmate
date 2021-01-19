from functools import lru_cache

from checkmate.url.domain._domain_core import DomainCore
from checkmate.url.domain.public_suffix import PublicSuffix
from checkmate.url.domain.top_level_domain import TopLevelDomain


class Domain(DomainCore):
    """Represent a domain string with metadata."""

    # This class differs from DomainCore, in that it stitches together a lot of
    # information from other classes. The DomainCore is needed to allow those
    # classes to make use of some of the basic functionality without getting in
    # an import loop.

    @property
    def is_public(self):
        """Get whether the domain is publicly available."""

        if self.is_ip_v4:
            return not self.is_private_ip_v4

        return self.is_fully_qualified

    @property
    @lru_cache(1)
    def is_fully_qualified(self):
        """Get whether the domain is a fully qualified domain name (public).

        IP addresses are not considered fully qualified, as they have no top
        level domain.
        """

        if not self.is_valid:
            return False

        # We have a proper suffix, and it's not the whole domain name
        return bool(self.icann_suffix) and (self != self.icann_suffix)

    @property
    def tld(self):
        """Get the top level domain (if any)."""

        if TopLevelDomain.is_tld(self):
            return str(self)

        return TopLevelDomain.get_tld(self)

    @property
    def public_suffix(self):
        """Get the public suffix for this domain.

        This includes recognised suffixes from ICANN (such as `co.uk`) and
        private companies (`github.io`). In many cases this will be identical
        to the top level domain.
        """

        if self.is_ip_v4:
            return None

        return PublicSuffix.get_suffix(self, icann_only=False)

    @property
    def icann_suffix(self):
        """Get the ICANN registered suffix for this domain.

        This includes recognised suffixes from ICANN (such as `co.uk`) but not
        private companies.
        """
        if self.is_ip_v4:
            return None

        return PublicSuffix.get_suffix(self, icann_only=True)

    @property
    def suffix_type(self):
        """Get the suffix type of this domain (if any).

        This will tell you if the domain has a private, or ICANN recognised
        suffix. All private suffixes will have a ICANN recognised suffix in
        addition.
        """
        if self.is_ip_v4:
            return None

        return PublicSuffix.suffix_type(PublicSuffix.get_suffix(self))

    @lru_cache(2)
    def split_domain(self, icann_only=False):
        """Split a domain into a root domain and sub-domain labels.

        For example:
            a.b.c.co.uk -> ["a", "b"], "c.co.uk"

        In the case of an IP address or a domain string consisting of only a
        suffix, this will result in empty subdomains and the domain value
        returned as the root domain.

        :param icann_only: Only include ICANN recognised suffixes, not private
            ones
        :returns: A tuple consisting of (a list of sub-domain labels, root domain)
        """
        if self.is_ip_v4:
            return [], str(self)

        suffix = PublicSuffix.get_suffix(self, icann_only)
        if not suffix or suffix == self:
            return [], str(self)

        labels = self[: -len(suffix) - 1].split(".")
        root_domain = f"{labels[-1]}.{suffix}"

        return labels[:-1], root_domain

    @property
    def root_domain(self):
        """Get the root domain without any sub-domains.

        Domains with different root domains can be considered different (but
        possibly related) sites.

        For example:

            www.google.com -> google.com
            a.b.c.github.io -> c.github.io
        """
        _, root_domain = self.split_domain(icann_only=False)

        return root_domain

    def as_dict(self):
        suffix_type = self.suffix_type

        return {
            "domain": str(self),
            "meta": {
                "is_valid": self.is_valid,
                "is_public": self.is_public,
                "is_fully_qualified": self.is_fully_qualified,
                "is_ip_v4": self.is_ip_v4,
                "is_private_ip_v4": self.is_private_ip_v4,
            },
            "split_domain": self.split_domain(),
            "root_domain": self.root_domain,
            "suffix": {
                "type": None if suffix_type is None else suffix_type.value,
                "tld": self.tld,
                "public": self.public_suffix,
                "icann": self.icann_suffix,
            },
        }
