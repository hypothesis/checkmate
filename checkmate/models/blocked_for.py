from enum import Enum


class BlockedFor(Enum):
    GENERAL = "general"
    LMS = "lms"

    @classmethod
    def parse(cls, value):
        """Parse a value into an enum object."""
        try:
            return cls(value)
        except ValueError:
            return cls.GENERAL

    @property
    def extra_args(self):
        args = {
            "display_how_to_access": True,
            "annotated_with": "Via",
        }

        if self == self.LMS:
            args["display_how_to_access"] = False
            args["annotated_with"] = "Hypothesis"

        return args
