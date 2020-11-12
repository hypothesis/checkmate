from checkmate.views.api.url_check import url_check


class TestURLCheck:
    def test_a_good_url(self, make_request):
        request = make_request("/api/url", {"url": "http://happy.example.com"})

        result = url_check(request)

        assert result.status_code == 204
