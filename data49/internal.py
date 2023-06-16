# TODO: Module-level __getattr__
# pylint: disable=C
import warnings
from typing import TypeVar

from thefuzz import process

T = TypeVar("T")
A = TypeVar("A")


def _typo_safe_getattr(self: T, attr_name: str) -> A:
    items = dir(self)
    name = type(self).__name__
    found, confidence = process.extractOne(attr_name, items)
    if confidence <= 50:
        raise AttributeError(
            f"'{name}' object has no attribute '{attr_name}'. Did you mean: {', '.join((x[0] for x in process.extract(attr_name,items)))}?",
        )
    warnings.warn(
        f"'{name}' object has no attribute '{attr_name}'. I'm going to assume you meant '{found}'",
        stacklevel=2,
    )
    return getattr(self, found)


def add_typo_safety(some_class: T) -> T:
    if hasattr(some_class, "__getattr__"):
        raise TypeError(f"class '{some_class}' already implements '__getattr__'")

    some_class.__getattr__ = _typo_safe_getattr

    return some_class
