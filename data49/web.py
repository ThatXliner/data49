import contextlib
import enum
import functools
import importlib
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

from . import internal

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
    "Soup",  # TODO: Better name
]


def Soup(html: str, **kwargs) -> BeautifulSoup:
    """Convert a string to a BeautifulSoup object."""
    return BeautifulSoup(html, features="html.parser", **kwargs)


class BrowserType(enum.Enum):
    """An enumeration of supported browsers for :func:`get_browser`."""

    CHROME = {"name": "Chrome", "make_headless": lambda x: x.add_argument("--headless")}
    SAFARI = {"name": "Safari", "make_headless": None}
    FIREFOX = {
        "name": "Firefox",
        "make_headless": lambda x: x.add_argument("-headless"),
    }


__get_browser_cache: Dict[
    Tuple[Tuple[BrowserType, ...], bool, Optional[Tuple[str, ...]]],
    Optional[RawWebDriver],
] = {}


def get_browser(
    priority: Tuple[BrowserType, ...] = (
        BrowserType.CHROME,
        BrowserType.FIREFOX,
        BrowserType.SAFARI,
    ),
    headless: bool = True,
    arguments: Optional[Sequence[str]] = None,
) -> RawWebDriver:
    """Lil' helper function that attempts to get a valid WebDriver."""
    _cache_key = (
        tuple(enum.name for enum in priority),
        headless,
        tuple(arguments) if arguments is not None else None,
    )
    if _cache_key in __get_browser_cache:
        output = __get_browser_cache[_cache_key]
        if output is None:
            raise RuntimeError("Could not find any browser that supports your needs")
        return output
    #   if output is None:
    #   pass

    def _(browser_name: BrowserType) -> Optional[RawWebDriver]:
        try:
            # TODO: Import directly from selenium.webdriver
            options = importlib.import_module(
                ".options",
                f"selenium.webdriver.{browser_name.value['name'].lower()}",
            ).Options()
            if headless:
                try:
                    browser_name.value["make_headless"](options)
                except TypeError:
                    return None
            if arguments:
                for arg in arguments:
                    options.add_argument(arg)
            service = importlib.import_module(
                ".service",
                f"selenium.webdriver.{browser_name.value['name'].lower()}",
            ).Service(log_path=os.devnull)
            browser = functools.partial(
                getattr(drivers, browser_name.value["name"]),
                options=options,
                service=service,
            )
            # There is no better way to check validity
            # than to open and close it...
            browser().close()
        except browser_exceptions.WebDriverException:
            return None
        else:
            return browser

    for browser in priority:
        found = _(browser)
        if found is not None:
            __get_browser_cache[_cache_key] = found
            return found
    __get_browser_cache[_cache_key] = None
    # TODO: Download geckodriver/chromedriver and use it
    raise RuntimeError("Could not find any browser that supports your needs")


@internal.add_typo_safety
@dataclass
class Element:
    """Represents a DOM element.

    Should not be instantiated directly but instead with methods like :meth:`BrowserContext.query_selector`
    """

    webelement: webelement.WebElement

    def soup(self) -> BeautifulSoup:
        """Convert the element into a BeautifulSoup object."""
        return Soup(self["innerHTML"])

    @property
    @functools.lru_cache
    def name(self) -> str:
        """Name of the element. (e.g. 'a' or 'div')."""
        return self.webelement.tag_name

    # get_attribute documentation says it may return booleans...
    # @functools.lru_cache()
    def get(self, attr: str) -> Optional[str]:
        """Get the IDL attribute of this element (e.g. `innerHTML`, `value`)."""
        return self.webelement.get_attribute(attr)  # type: ignore

    # TODO: Use soup and cache soup
    # To avoid selenium.common.exceptions.StaleElementReferenceException
    def __getitem__(self, attr: str) -> str:
        """Like :meth:`get` but doesn't return None."""
        output = self.get(attr)
        if output is None:
            raise KeyError(attr)
        return output

    def click(self) -> None:
        """Simulate a user click on this element."""
        self.webelement.click()  # type: ignore

    def type(self, keys: str) -> None:
        """Simulate a user typing stuff on this element. Examples include filling out a form or text input."""
        self.webelement.send_keys(keys)  # type: ignore


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
            :meth:`wait` instead (or :meth:`css`, which combines this with :meth:`wait`).

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
            expected_conditions.presence_of_element_located(  # type: ignore
                (By.CSS_SELECTOR, css_selector),
            ),
            wait_up_to,
        )

    # TODO: css_all

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
            raise TimeoutError(
                f"Could not find element under {up_to} seconds",
            ) from error

    # def wait_until  # Recieves a function that returns boolean as parameter. Polls.


@internal.add_typo_safety
@dataclass
class Browser(contextlib.AbstractContextManager):
    """>>> with Browser("https://google.com"): pass
    >>> with Browser("https://google.com", driver=get_browser(priority=(BrowserType.FIREFOX,))):
    ...     pass
    >>> from selenium import webdriver
    >>> from selenium.webdriver.firefox.options import Options
    >>> with Browser("https://google.com", driver=lambda: webdriver.Firefox(options=Options)):
    ...     pass
    >>> with Browser("https://google.com", driver=webdriver.Ie): pass.
    """

    url: str
    driver: Callable[[], RawWebDriver] = field(default_factory=get_browser)

    def open(self) -> BrowserContext:
        """Start the browser."""
        self.driver = self.driver()  # XXX: Don't make Browsers one-time
        tries = 42  # Arbitrary number of tries
        while tries > 0:
            try:
                self.driver.get(self.url)
                break
            except browser_exceptions.WebDriverException:
                tries -= 1
                continue
        if tries == 0:
            raise RuntimeError("Could not load URL")
        return BrowserContext(self.url, self.driver)

    def close(self) -> None:
        """Close the browser."""
        self.driver.close()

    def __enter__(self) -> BrowserContext:
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
