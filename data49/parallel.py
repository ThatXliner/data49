# NOT FINISHED
# For parallism, use that library numpy and friends use


import concurrent.futures
import functools
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Tuple, Union

import attr

from . import internal

__all__: List[str] = ["Bundle", "Sluice", "Pipeline"]


@attr.s(auto_attribs=True)
class Bundle:
    """Bundling functions together for running.

    If you want to use this with the :class:`Sluice`, try
    using tuples to group functions instead
    """

    functions: Iterable[Callable]
    chain: bool = False
    first: Any = None

    def __call__(self):
        if self.chain:
            output = None
            for i, func in enumerate(self.functions):
                if i == 0:  # first func
                    output = func(self.first) if self.first is not None else func()
                else:
                    output = func(output)
            return output
        for func in self.functions:
            func()
        return None


@internal.add_typo_safety
@dataclass
class Sluice:
    """Make pipelines painless. Even parallel if you want to.

    The idea is this:

    You have functions "a" and "b":

    >>> def a():
    ...   print("A was ran")
    >>> def b():
    ...   print("B was ran")


    Running them synchronously
    --------------------------

    >>> import data49 as d
    >>> pipeline = d.Sluice([a, b])
    >>> pipeline.run()  # Typo tolerant!
    A was ran
    B was ran

    Or painlessly asynchronous
    --------------------------

    >>> import data49 as d
    >>> pipeline = d.Sluice([a, b], concurrent=True)
    >>> pipeline.run()
    B was ran
    A was ran
    >>> pipeline.run()
    A was ran
    B was ran
    >>>  # Not deterministic

    """

    pipeline: Iterable[Union[Callable, Tuple[Callable]]]
    concurrent: bool = False
    chain: bool = False

    # Concurrency options
    use_threads: bool = True
    max_workers: int = 3

    def run(self) -> None:
        if self.concurrent:
            worker_type = (
                concurrent.futures.ThreadPoolExecutor
                if self.use_threads
                else concurrent.futures.ProcessPoolExecutor
            )
            if self.chain:
                raise ValueError("Can only chain synchronously for now")
            with worker_type(max_workers=self.max_workers) as executor:
                for item in self.pipeline:
                    if isinstance(item, tuple):
                        executor.submit(Bundle(item))
                    else:
                        executor.submit(item)
            return None
        return Bundle(self.pipeline, chain=self.chain)()


Pipeline = functools.partial(Bundle, chain=True)
Pipeline.__doc__ = (
    """:class:`Bundle` but chaining. For functional-programming pipelines"""
)
