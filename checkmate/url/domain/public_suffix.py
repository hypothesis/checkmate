"""Rules and tests for public domain suffixes."""

from collections import namedtuple

from checkmate.url.domain._data import load_data
from checkmate.url.domain.enums import SuffixType


class PublicSuffix:
    """Rules around public suffixes for domains.

    These come in two basic flavours:

     * ICANN - .com, .co.uk etc.
     * Private - .github.io

    The private list includes lots of blog sites and domain hosting providers
    etc. In this context "private" and "public" are being used in different
    ways. We mean "public" as in on the internet and "private" as in privately
    owned. So a "private" suffix in this context is "public" as well because
    it is publicly accessible.

    This data is sourced from and maintained by: https://publicsuffix.org/list/
    """

    # Populated by _load() below
    RULES = {}
    LONGEST_RULE = 0

    # A small object to hold our rules and give them nice properties to access
    Rule = namedtuple("Rule", ["line_no", "is_exception", "type"])

    @classmethod
    def suffix_type(cls, suffix):
        """Get the suffix classification of the given domain suffix.

        This will either be:

         * DomainSuffix.Type.ICANN - For real deal ICANN domain suffixes
         * DomainSuffix.Type.Private - For those maintained by private
         companies

        :return: A DomainSuffix.Type or None if this isn't a domain suffix.
        """
        if not suffix:
            return None

        # We need to match the exact suffix as well as the wild card version
        matching_rule = cls.RULES.get(suffix)
        wild_rule = cls.RULES.get(cls._make_wild(suffix))

        if matching_rule and wild_rule:
            # If we get a hit for both, we need to pick the one which happened
            # last in the ruleset according to the rules. In practice this
            # never seems to happen as the wild version is always first.

            if wild_rule.line_no > matching_rule.line_no:  # pragma: no cover
                matching_rule = wild_rule
        else:
            matching_rule = matching_rule or wild_rule

        if not matching_rule or matching_rule.is_exception:
            return None

        return matching_rule.type

    @classmethod
    def is_suffix(cls, suffix, icann_only=False):
        """Find out if the given suffix is a recognised public suffix.

        :param suffix: Suffix to test
        :param icann_only: Limit the results to ICANN suffixes only
        :rtype: bool
        """

        suffix_type = PublicSuffix.suffix_type(suffix)
        if not suffix_type:
            return False

        if icann_only and suffix_type != SuffixType.ICANN:
            return False

        return True

    @classmethod
    def has_suffix(cls, domain):
        """Find out if the given domain has a recognised public suffix.

        :param domain: Domain object to test
        :rtype: bool
        """
        return bool(cls.get_suffix(domain))

    @classmethod
    def get_suffix(cls, domain, icann_only=False):
        """Get the public suffix from a domain.

        :param domain: Domain object to retrieve suffix from
        :param icann_only: Limit the results to ICANN suffixes only
        :return: The public suffix or None
        """

        # This will be in shortest first ['com', 'blah.com']
        suffixes = list(domain.suffixes(max_depth=cls.LONGEST_RULE))

        # Reverse here so we check for longer things first:
        for suffix in reversed(suffixes):
            if cls.is_suffix(suffix, icann_only):
                return suffix

        return None

    @classmethod
    def parse_rules(cls, lines):
        # See https://publicsuffix.org/list/ for details of the format

        rules = {}
        max_dots = 0

        suffix_type = SuffixType.ICANN

        for line_no, line in enumerate(lines):
            if "===BEGIN PRIVATE DOMAINS===" in line:
                # Pylint is being weird about changing from one enum to another
                # pylint: disable=redefined-variable-type
                suffix_type = SuffixType.PRIVATE
                continue

            # This is white space or a comment
            if not line or line.startswith("//"):
                continue

            is_exception = False

            # Lines starting with "!" are exception rules
            if line.startswith("!"):
                line = line.lstrip("!")
                is_exception = True

            max_dots = max(max_dots, line.count("."))

            rules[line] = cls.Rule(line_no, is_exception, suffix_type)

        return rules, max_dots + 1

    @classmethod
    def _make_wild(cls, suffix):
        # Technically the rules can include more than one '*', in any position
        # but they actually don't at the moment. They are always a single
        # prefix
        labels = suffix.split(".")
        labels[0] = "*"
        return ".".join(labels)

    @classmethod
    def _load(cls):
        # Some slightly odd factoring here to make the rule parsing easy to
        # test. This could easily be here otherwise
        cls.RULES, cls.LONGEST_RULE = cls.parse_rules(
            load_data("resource/data/public_suffix_list.dat")
        )


PublicSuffix._load()  # pylint: disable=protected-access
