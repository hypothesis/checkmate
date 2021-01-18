from unittest.mock import sentinel

import pytest
from h_matchers import Any

from checkmate.models import Reason
from checkmate.services.url_checker import URLCheckerService, factory
from checkmate.url import hash_url


class TestURLCheckerService:
    def test_it_calls_sub_checkers(self, checker, URLHaus, CustomRules, AllowRules):
        URLHaus.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)
        CustomRules.return_value.check_url.return_value = (Reason.MALICIOUS,)
        AllowRules.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)

        results = checker.check_url("http://example.com", fail_fast=False)

        # Deduped and sorted worst first
        assert list(results) == [Reason.MALICIOUS, Reason.NOT_ALLOWED]

        url_hashes = list(hash_url("http://example.com"))

        for sub_checker in (URLHaus, CustomRules, AllowRules):
            sub_checker.return_value.check_url.assert_called_once_with(url_hashes)

    def test_it_can_fail_fast(self, checker, URLHaus, CustomRules, AllowRules):
        URLHaus.return_value.check_url.return_value = (Reason.MALICIOUS,)

        results = checker.check_url("http://example.com", fail_fast=True)

        assert list(results) == [Reason.MALICIOUS]

        CustomRules.return_value.check_url.assert_not_called()
        AllowRules.return_value.check_url.assert_not_called()

    def test_it_only_fails_fast_for_mandatory(
        self, checker, URLHaus, CustomRules, AllowRules
    ):
        URLHaus.return_value.check_url.return_value = (Reason.OTHER,)
        CustomRules.return_value.check_url.return_value = (Reason.HIGH_IO,)
        AllowRules.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)

        results = checker.check_url("http://example.com", fail_fast=True)

        assert (
            list(results)
            == Any.list.containing(
                [Reason.OTHER, Reason.HIGH_IO, Reason.NOT_ALLOWED]
            ).only()
        )

    def test_it_can_disable_the_allow_list(
        self, checker, URLHaus, CustomRules, AllowRules
    ):
        AllowRules.return_value.check_url.return_value = (Reason.NOT_ALLOWED,)

        checker.check_url("http://example.com", allow_all=True, fail_fast=False)

        AllowRules.return_value.check_url.assert_not_called()

    @pytest.fixture
    def checker(self, db_session):
        return URLCheckerService(db_session)

    @pytest.fixture
    def patch_checker(self, patch):
        """Return a function for patching a checker class."""

        def patch_checker(checker_class):
            checker_cls = patch(f"checkmate.services.url_checker.{checker_class}")
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


class TestFactory:
    # Some basic sanity
    def test_it(self, pyramid_request):
        service = factory(sentinel.context, pyramid_request)

        assert isinstance(service, URLCheckerService)
