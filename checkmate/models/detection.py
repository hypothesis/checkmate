from checkmate.models.reason import Reason
from checkmate.models.source import Source


class Detection:
    """A model for a detection in our rulesets."""

    def __init__(self, reason, source):
        """Create a new rule detection object.

        :param reason: Reason object for why this detection happened
        :param source: Source onject for where this detection came from
        """
        assert isinstance(reason, Reason)
        assert isinstance(source, Source)

        self.reason = reason
        self.source = source

    @property
    def severity(self):
        """Get how bad this detection is.

        :rtype: Severity
        """

        return self.reason.severity

    def __repr__(self):
        return f"{self.__class__.__name__}({self.reason}, {self.source})"

    def __eq__(self, other):
        if not isinstance(other, Detection):
            return False

        return (other.reason, other.source) == (self.reason, self.source)
