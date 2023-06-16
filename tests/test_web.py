from data49 import web


def test_request():
    ...


class TestHeadless:
    def test_browser(self):
        with web.Browser("https://google.com") as browser:
            pass

    def test_browser_alternate(self):
        b = web.Browser("https://google.com")
        b.open()
        b.close()


class TestNoHeadless:
    def test_browser(self):
        with web.Browser(
            "https://google.com", driver=web.get_browser(headless=False)
        ) as _:
            pass

    def test_browser_alternate(self):
        b = web.Browser("https://google.com", driver=web.get_browser(headless=False))
        b.open()
        b.close()
