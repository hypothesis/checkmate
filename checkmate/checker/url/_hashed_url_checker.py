from abc import ABC, abstractmethod


class HashedURLChecker(ABC):
    """Abstract base class for URL checkers which operate on hex hashes."""

    def __init__(self, session):
        """Create a new checking object.

        :param session: A DB session to work in
        """
        self._session = session

    @abstractmethod
    def check_url(self, hex_hashes):
        """Check for reasons to block a URL based on it's hashes.

        :param hex_hashes: A list of hashes for a URL
        :returns: A generator of Reason objects
        """
