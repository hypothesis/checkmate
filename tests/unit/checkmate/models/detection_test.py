import pytest

from checkmate.models import Reason, Source
from checkmate.models.detection import Detection


class TestDetection:
    @pytest.mark.parametrize(
        "reason,source", ((Reason.OTHER, "bad"), ("bad", Source.URL_HAUS))
    )
    def test_it_explodes_with_bad_inputs(self, reason, source):
        with pytest.raises(AssertionError):
            Detection(reason, source)

    @pytest.mark.parametrize(
        "reason",
        (
            Reason.OTHER,
            Reason.MALICIOUS,
        ),
    )
    def test_it_passes_through_severity(self, reason):
        detection = Detection(reason, Source.URL_HAUS)

        assert detection.severity == reason.severity

    @pytest.mark.parametrize(
        "other,equal",
        (
            (Detection(Reason.MALICIOUS, Source.URL_HAUS), True),
            (Detection(Reason.MALICIOUS, Source.ALLOW_LIST), False),
            (Detection(Reason.OTHER, Source.URL_HAUS), False),
            ("not_a_detection", False),
        ),
    )
    def test_equals(self, other, equal):
        detection = Detection(Reason.MALICIOUS, Source.URL_HAUS)

        assert (detection == other) == equal

    def test_repr(self):
        detection = Detection(Reason.MALICIOUS, Source.URL_HAUS)

        assert "Detection" in repr(detection)
        assert "MALICIOUS" in repr(detection)
        assert "URL_HAUS" in repr(detection)
