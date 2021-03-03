"""A collection of reasons URLs can be blocked (and friends)."""

from enum import Enum
from functools import total_ordering


@total_ordering
class OrderedEnum(Enum):
    """Enumerations which compare and sort in the order they are defined."""

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError("Can only compare an enum with another instance of itself")

        if self == other:
            return False

        for item in type(self).__members__.values():
            if item == self:
                return True
            if item == other:
                return False

        # Shouldn't really be possible
        return False  # pragma: no cover


class Severity(OrderedEnum):
    """List of level of severity of a block."""

    # These items can be blocked, or not, at the discretion of the service
    ADVISORY = "advisory"
    # These items must be blocked by all services
    MANDATORY = "mandatory"


class Reason(Enum):
    """List of reasons a URL can be blocked."""

    MALICIOUS = "malicious"  # Actively hostile content of some kind
    PUBLISHER_BLOCKED = "publisher-blocked"  # Content owner has asked us to block
    MEDIA_VIDEO = "media-video"  # Sites which are mostly video content
    MEDIA_AUDIO = "media-audio"  # Sites which are mostly audio content
    MEDIA_IMAGE = "media-image"  # Sites which are mostly image content
    MEDIA_MIXED = "media-mixed"  # Sites with a mixture of content
    HIGH_IO = "high-io"  # Sites with high interactivity and AJAX calls

    NOT_ALLOWED = "not-explicitly-allowed"  # Not on the allow list

    OTHER = "other"  # Escape hatch for poorly formatted values

    @property
    def severity(self):
        """Get the severity of this reason."""

        if self in (self.MALICIOUS, self.PUBLISHER_BLOCKED):
            return Severity.MANDATORY

        return Severity.ADVISORY

    @classmethod
    def parse(cls, value, default=OTHER):
        """Parse a value into an enum object."""
        value = value.strip() if value else value
        try:
            return cls(value)
        except ValueError:
            if default:
                return cls(default)

            raise

    def serialise(self):
        """Convert to a JSON API resource object."""

        # https://jsonapi.org/format/#document-resource-objects
        return {
            "type": "reason",
            "id": self.value,
            "attributes": {
                # pylint: disable=no-member
                # pylint is just confused... not sure why
                "severity": self.severity.value
            },
        }
