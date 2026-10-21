import contextlib
import enum
import functools
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import selenium.common.exceptions as browser_exceptions
from bs4 import BeautifulSoup
from requests import get, post  # As for API
from selenium import webdriver as drivers
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webdriver, webelement
from selenium.webdriver.support import expected_conditions  # As for API
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore[attr-defined]

from . import _browser_security, _driver_manager, internal

RawWebDriver = webdriver.WebDriver
__all__ = [
    "get_browser",
    "Browser",
    "BrowserType",
    "BrowserContext",
    "browser_exceptions",
    "Element",
    "RawWebDriver",
    "expected_conditions",
    "get",
    "post",
    "to_soup",  # TODO(ThatXliner): Better name
    "Soup",  # TODO(ThatXliner): Better name
    "BrowserSecurityError",
]

BrowserSecurityError = _browser_security.BrowserSecurityError


def to_soup(html: str, **kwargs) -> BeautifulSoup:
    """Convert a string to a BeautifulSoup object."""
    return BeautifulSoup(html, features="html.parser", **kwargs)


Soup = to_soup


class BrowserType(enum.Enum):
    """An enumeration of supported browsers for :func:`get_browser`."""

    CHROME = {"name": "Chrome", "make_headless": lambda x: x.add_argument("--headless")}
    SAFARI = {"name": "Safari", "make_headless": None}
    FIREFOX = {
        "name": "Firefox",
        "make_headless": lambda x: x.add_argument("-headless"),
    }


__get_browser_cache: Dict[
    Tuple[Tuple[str, ...], bool, Optional[Tuple[str, ...]]],
    Optional[Callable[[], RawWebDriver]],
] = {}


def _start_verified_browser(*, options, service):
    _browser_security.require_safe_arguments(options.arguments)
    if options.capabilities.get("acceptInsecureCerts") is not False:
        msg = "Browser TLS certificate validation must be enabled"
        raise BrowserSecurityError(msg)
    prefs = options.experimental_options.get("prefs")
    if (
        not isinstance(prefs, dict)
        or prefs.get(_browser_security.PLATFORM_TRUST_PREF) is not False
    ):
        msg = "Browser platform trust integration must be disabled"
        raise BrowserSecurityError(msg)
    browser = drivers.Chrome(options=options, service=service)
    try:
        _browser_security.require_safe_chrome(browser)
    except browser_exceptions.WebDriverException as error:
        browser.quit()
        msg = "Browser trust inspection failed or is unsupported"
        raise BrowserSecurityError(msg) from error
    except Exception:
        browser.quit()
        raise
    return browser


def _try_to_get(
    browser_name: BrowserType,
    headless: bool,
    arguments: Optional[Sequence[str]],
) -> Optional[Callable[[], RawWebDriver]]:
    if browser_name is not BrowserType.CHROME:
        msg = (
            "Only current Chrome has a verified automatic browser trust path. "
            "Firefox and Safari are blocked before application navigation."
        )
        raise BrowserSecurityError(msg)
    _browser_security.require_safe_arguments(arguments)
    try:
        options = drivers.ChromeOptions()
        options.set_capability("acceptInsecureCerts", False)
        options.add_experimental_option(
            "prefs",
            {_browser_security.PLATFORM_TRUST_PREF: False},
        )
        if headless:
            options.add_argument("--headless")
        if arguments:
            for arg in arguments:
                options.add_argument(arg)
        explicit_browser = os.environ.get("SE_CHROME_PATH", "")
        if explicit_browser:
            paths = _driver_manager.driver_paths("chrome", explicit_browser)
        else:
            paths = _driver_manager.driver_paths(
                "chrome",
                browser_version=_browser_security.PINNED_CHROME_VERSION,
                force_browser_download=True,
            )
        if paths.get("browser_path"):
            options.binary_location = paths["browser_path"]
        service = drivers.ChromeService(
            executable_path=paths["driver_path"],
            log_output=os.devnull,
        )
        browser = functools.partial(
            _start_verified_browser,
            options=options,
            service=service,
        )
        # There is no better way to check validity
        # than to open and close it...
        browser().quit()
    except BrowserSecurityError:
        raise
    except browser_exceptions.WebDriverException as error:
        msg = (
            "Could not resolve or start the pinned secure Chrome runtime. "
            "The platform or browser download may be unsupported."
        )
        raise BrowserSecurityError(msg) from error
    else:
        return browser


def get_browser(
    priority: Tuple[BrowserType, ...] = (BrowserType.CHROME,),
    headless: bool = True,
    arguments: Optional[Sequence[str]] = None,
) -> Callable[[], RawWebDriver]:
    """Return a factory that checks browser certificate trust before navigation.

    Requires Chrome 158.0.8115.0 or later with updated root data. Set
    SE_CHROME_PATH to select an official current browser executable.
    """
    _cache_key = (
        tuple(enum.name for enum in priority),
        headless,
        tuple(arguments) if arguments is not None else None,
    )
    if _cache_key in __get_browser_cache:
        output = __get_browser_cache[_cache_key]
        if output is None:
            msg = "Could not find any browser that supports your needs"
            raise RuntimeError(msg)
        return output
    for browser in priority:
        found = _try_to_get(browser, headless, arguments)
        if found is not None:
            __get_browser_cache[_cache_key] = found
            return found
    __get_browser_cache[_cache_key] = None
    # TODO(ThatXliner): Download geckodriver/chromedriver and use it
    msg = "Could not find any browser that supports your needs"
    raise RuntimeError(msg)


@internal.add_typo_safety
@dataclass
class Element:
    """Represents a DOM element.

    Should not be instantiated directly but instead
    with methods like :meth:`BrowserContext.query_selector`
    """

    webelement: webelement.WebElement

    def soup(self) -> BeautifulSoup:
        """Convert the element into a BeautifulSoup object."""
        return to_soup(self["innerHTML"])

    @functools.cached_property
    def name(self) -> str:
        """Name of the element. (e.g. 'a' or 'div')."""
        return self.webelement.tag_name

    # get_attribute documentation says it may return booleans...
    # @functools.lru_cache()
    def get(self, attr: str) -> Optional[str]:
        """Get the IDL attribute of this element (e.g. `innerHTML`, `value`)."""
        return self.webelement.get_attribute(attr)

    # TODO(ThatXliner): Use soup and cache soup
    # To avoid selenium.common.exceptions.StaleElementReferenceException
    def __getitem__(self, attr: str) -> str:
        """Like :meth:`get` but doesn't return None."""
        output = self.get(attr)
        if output is None:
            raise KeyError(attr)
        return output

    def click(self) -> None:
        """Simulate a user click on this element."""
        self.webelement.click()

    def type(self, keys: str) -> None:  # noqa: A003
        """Simulate a user typing stuff on this element.

        Examples include filling out a form or text input."""
        self.webelement.send_keys(keys)


@internal.add_typo_safety
@dataclass
class BrowserContext:
    url: str
    driver: RawWebDriver
    _waits: Dict[float, WebDriverWait] = field(default_factory=dict)

    def go(self, to: str) -> None:
        """Change the current URL to `to`."""
        self.driver.get(to)

    def set_url(self, url: str) -> None:
        """Alias of :meth:`go`."""
        self.go(url)

    def back(self) -> None:
        """Go back one page in browser history."""
        self.driver.back()

    def query_selector(self, css_selector: str) -> Element:
        """Instantly find an element that matches the given CSS selector.

        .. note::

            If the element you want to find isn't readily available, you can use
            :meth:`wait` instead (or :meth:`css`, which combines this with :meth:`wait`)

        Args:
            css_selector (str): The CSS selector to match

        Returns
        -------
            Element: The element found by the given CSS selector

        Raises
        ------
            NoElementException: The element doesn't exist

        """
        return Element(self.driver.find_element(By.CSS_SELECTOR, css_selector))

    def css(self, css_selector: str, wait_up_to: float = 10.0) -> Element:
        """Find something with CSS with a timeout.

        Args:
            css_selector (str): The CSS selector to find an element
            wait_up_to (float): self-explanatory

        Returns
        -------
            Element: The element found

        Raises
        ------
            TimeoutError: Timed out

        See Also
        --------
             :meth:`wait`
        """
        return self.wait(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, css_selector),
            ),
            wait_up_to,
        )

    def query_selector_all(self, css_selector: str) -> List[Element]:
        """:meth:`query_selector` for multiple elements."""
        return list(
            map(Element, self.driver.find_elements(By.CSS_SELECTOR, css_selector)),
        )

    def js(self, javascript: str, *args) -> Any:
        """Run JavaScript."""
        return self.driver.execute_script(javascript, *args)

    def run_script(self, javascript: str, *args) -> Any:
        """Alias for :meth:`js`."""
        return self.js(javascript, *args)

    def _get_wait_up_to(self, seconds: float) -> WebDriverWait:
        if seconds not in self._waits:
            self._waits[seconds] = WebDriverWait(self.driver, seconds)
        return self._waits[seconds]

    def wait(
        self,
        until: Callable[[RawWebDriver], Union[webelement.WebElement, bool]],
        up_to: float = 10.0,
    ) -> Element:
        """Wait until an element is located.

        Returns that `Element` if found under `up_to`, the time limit in seconds.

        Raises `TimeoutError` if the element is not found in time.

        Args:
            until (Callable[[RawWebDriver], Union[webelement.WebElement, bool]]):
                        An object that when `__call__` is called,
                        return `False` indicating that the element was not found
                        or the `selenium.webdriver.remote` when found.
                        You may use Selenium's `expected_conditions`.
            up_to (float): The time limit in seconds. Defaults to 10.0.

        Returns
        -------
            Element: The element that was found

        Raises
        ------
            TimeoutError: The element was not found in time.

        """
        try:
            return Element(self._get_wait_up_to(up_to).until(until))
        except browser_exceptions.TimeoutException as error:
            msg = f"Could not find element under {up_to} seconds"
            raise TimeoutError(msg) from error

    # def wait_until  # Recieves a function that returns boolean as parameter. Polls.


@internal.add_typo_safety
@dataclass
class Browser(contextlib.AbstractContextManager):
    """Open a page after the automatic browser's certificate checks pass.

    Custom get_driver callables require allow_unverified_driver=True, which
    explicitly bypasses Data49's browser certificate safeguards.

    >>> with Browser("https://example.com"): pass
    """

    url: str
    get_driver: Callable[[], RawWebDriver] = field(default_factory=get_browser)
    allow_unverified_driver: bool = False

    def open(self) -> BrowserContext:  # noqa: A003
        """Start the browser."""
        if not self.allow_unverified_driver and not (
            isinstance(self.get_driver, functools.partial)
            and self.get_driver.func is _start_verified_browser
        ):
            msg = (
                "A custom unverified get_driver bypasses Data49's browser security "
                "checks. Use get_browser(), or explicitly accept responsibility "
                "with allow_unverified_driver=True."
            )
            raise BrowserSecurityError(msg)
        self.driver = (
            self.get_driver()
        )  # TODO(ThatXliner): Don't make Browsers one-time
        tries = 42  # Arbitrary number of tries
        while tries > 0:
            try:
                self.driver.get(self.url)
                break
            except browser_exceptions.WebDriverException:
                tries -= 1
                continue
        if tries == 0:
            msg = "Could not load URL"
            raise RuntimeError(msg)
        return BrowserContext(self.url, self.driver)

    def close(self) -> None:
        """Close the browser."""
        self.driver.quit()

    def __enter__(self) -> BrowserContext:
        return self.open()

    def __exit__(self, *_):
        self.close()
