import os

import pytest

from data49 import web

pytestmark = pytest.mark.skipif(
    os.environ.get("DATA49_LIVE_BROWSER_TESTS") != "1",
    reason="Live browser tests require an explicitly enabled network/browser session",
)


def test_request():
    ...


class TestHeadless:
    def test_browser(self):
        with web.Browser("https://example.com") as _:
            pass

    def test_browser_alternate(self):
        b = web.Browser("https://example.com")
        b.open()
        b.close()


@pytest.mark.skipif(
    os.environ.get("DATA49_HEADFUL_TESTS") != "1",
    reason="Visible browser tests require an explicitly enabled desktop session",
)
class TestNoHeadless:
    def test_browser(self):
        with web.Browser(
            "https://example.com",
            get_driver=web.get_browser(headless=False),
        ) as _:
            pass

    def test_browser_alternate(self):
        b = web.Browser(
            "https://example.com",
            get_driver=web.get_browser(headless=False),
        )
        b.open()
        b.close()
