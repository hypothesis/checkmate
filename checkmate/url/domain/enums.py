from enum import Enum


class SuffixType(Enum):
    """Types of domain suffixes.

    All of these are "public" in the sense of accessible on the internet, but
    some are proper ICANN suffixes (co.uk) and others are owned and run by
    private entities (github.io)
    """

    ICANN = "icann"
    PRIVATE = "private"
