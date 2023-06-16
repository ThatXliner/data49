import types

import pytest

from data49 import internal


def test_insane_typo():
    @internal.add_typo_safety
    class e(types.SimpleNamespace):
        pass

    my_stuff = e(banana="BBB", boar="boring")
    with pytest.raises(AttributeError):
        my_stuff.freshavacdo


def test_cannot_add_typo_safety():
    with pytest.raises(TypeError, match="already implements '__getattr__'"):

        @internal.add_typo_safety
        class e:
            def __getattr__(self, name):
                pass
