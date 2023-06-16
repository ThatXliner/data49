# TODO(ThatXliner): Module-level __getattr__
# pylint: disable=C
import warnings
from typing import TypeVar

from thefuzz import process

T = TypeVar("T")
A = TypeVar("A")

MINIMUM_FUZZY_CONFIDENCE = 50


def _typo_safe_getattr(self: T, attr_name: str) -> A:
    items = dir(self)
    name = type(self).__name__
    found, confidence = process.extractOne(attr_name, items)
    if confidence <= MINIMUM_FUZZY_CONFIDENCE:
        msg = (
            f"'{name}' object has no attribute '{attr_name}'."
            " Did you mean: "
            + ", ".join(x[0] for x in process.extract(attr_name, items))
            + "?"
        )
        raise AttributeError(msg)
    warnings.warn(
        f"'{name}' object has no attribute '{attr_name}'."
        f" I'm going to assume you meant '{found}'",
        stacklevel=2,
    )
    return getattr(self, found)


def add_typo_safety(some_class: T) -> T:
    if hasattr(some_class, "__getattr__"):
        msg = f"class '{some_class}' already implements '__getattr__'"
        raise TypeError(msg)

    some_class.__getattr__ = _typo_safe_getattr

    return some_class
