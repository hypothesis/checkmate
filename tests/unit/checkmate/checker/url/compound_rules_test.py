import pytest
from h_matchers import Any

from checkmate.checker.url import CompoundRules
from checkmate.models import Reason
from checkmate.url import hash_url


class TestCompoundRules:
    def test_it_calls_sub_checkers(self, db_session, URLHaus, CustomRules, AllowRules):
        URLHaus.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)
        CustomRules.return_value.check_url.return_value = (Reason.MALICIOUS,)
        AllowRules.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)

        rules = CompoundRules(db_session, fail_fast=False)
        results = rules.check_url("http://example.com")

        # Deduped and sorted worst first
        assert list(results) == [Reason.MALICIOUS, Reason.NOT_ALLOWED]

        url_hashes = list(hash_url("http://example.com"))

        for checker in (URLHaus, CustomRules, AllowRules):
            checker.assert_called_once_with(db_session)
            checker.return_value.check_url.assert_called_once_with(url_hashes)

    def test_it_can_fail_fast(self, db_session, URLHaus, CustomRules, AllowRules):
        URLHaus.return_value.check_url.return_value = (Reason.MALICIOUS,)

        rules = CompoundRules(db_session, fail_fast=True)
        results = rules.check_url("http://example.com")

        assert list(results) == [Reason.MALICIOUS]

        CustomRules.assert_not_called()
        AllowRules.assert_not_called()

    def test_it_only_fails_fast_for_mandatory(
        self, db_session, URLHaus, CustomRules, AllowRules
    ):
        URLHaus.return_value.check_url.return_value = (Reason.OTHER,)
        CustomRules.return_value.check_url.return_value = (Reason.HIGH_IO,)
        AllowRules.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)

        rules = CompoundRules(db_session, fail_fast=True)
        results = rules.check_url("http://example.com")

        assert (
            list(results)
            == Any.list.containing(
                [Reason.OTHER, Reason.HIGH_IO, Reason.NOT_ALLOWED]
            ).only()
        )

    def test_it_can_disable_the_allow_list(
        self, db_session, URLHaus, CustomRules, AllowRules
    ):
        AllowRules.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)

        rules = CompoundRules(db_session, allow_all=True, fail_fast=False)
        rules.check_url("http://example.com")

        AllowRules.assert_not_called()

    @pytest.fixture
    def patch_checker(self, patch):
        """Return a function for patching a checker class."""

        def patch_checker(checker_class):
            checker_cls = patch(f"checkmate.checker.url.compound_rules.{checker_class}")
            checker_cls.return_value.check_url.return_value = tuple()
            return checker_cls

        return patch_checker

    @pytest.fixture(autouse=True)
    def AllowRules(self, patch_checker):
        return patch_checker("AllowRules")

    @pytest.fixture(autouse=True)
    def CustomRules(self, patch_checker):
        return patch_checker("CustomRules")

    @pytest.fixture(autouse=True)
    def URLHaus(self, patch_checker):
        return patch_checker("URLHaus")
