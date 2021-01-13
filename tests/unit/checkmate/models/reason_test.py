import operator

import pytest

from checkmate.models.reason import OrderedEnum, Reason, Severity


class TestOrderedEnum:
    class DummyEnum(OrderedEnum):
        """Enum for testing."""

        FIRST = 2
        MIDDLE = 3
        LAST = 1

    @pytest.mark.parametrize("l_pos,l_value", enumerate(DummyEnum))
    @pytest.mark.parametrize("r_pos,r_value", enumerate(DummyEnum))
    @pytest.mark.parametrize(
        "op",
        [operator.lt, operator.le, operator.eq, operator.ne, operator.ge, operator.gt],
    )
    # pylint: disable=too-many-arguments
    def test_comparison(self, l_pos, l_value, op, r_pos, r_value):
        assert op(l_value, r_value) is op(l_pos, r_pos)

    def test_it_fails_on_comparison_with_non_member(self):
        with pytest.raises(TypeError):
            assert self.DummyEnum.FIRST < 3


class TestSeverity:
    def test_it_sorts_correctly(self):
        assert Severity.ADVISORY < Severity.MANDATORY


class TestReason:
    @pytest.mark.parametrize(
        "value,reason",
        (
            ("malicious", Reason.MALICIOUS),
            ("publisher-blocked", Reason.PUBLISHER_BLOCKED),
            ("not a value", Reason.OTHER),
            (None, Reason.OTHER),
        ),
    )
    def test_it_can_parse(self, value, reason):
        assert Reason.parse(value) == reason

    @pytest.mark.parametrize(
        "reason,severity",
        (
            (Reason.MALICIOUS, Severity.MANDATORY),
            (Reason.PUBLISHER_BLOCKED, Severity.MANDATORY),
            (Reason.MEDIA_AUDIO, Severity.ADVISORY),
            (Reason.OTHER, Severity.ADVISORY),
        ),
    )
    def test_severity(self, reason, severity):
        assert reason.severity == severity

    def test_serialise(self):
        assert Reason.MALICIOUS.serialise() == {
            "type": "reason",
            "id": "malicious",
            "attributes": {
                "severity": "mandatory",
            },
        }
