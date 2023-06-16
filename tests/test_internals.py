import types

import pytest

from data49 import internal


def test_insane_typo():
    @internal.add_typo_safety
    class E(types.SimpleNamespace):
        pass

    my_stuff = E(banana="BBB", boar="boring")
    with pytest.raises(AttributeError):
        _ = my_stuff.freshavacdo


def test_cannot_add_typo_safety():
    with pytest.raises(TypeError, match="already implements '__getattr__'"):

        @internal.add_typo_safety
        class E:
            def __getattr__(self, name):
                pass
