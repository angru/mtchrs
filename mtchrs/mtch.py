"""Factory functions for composable equality matchers."""

import re as _re
import typing as _t
from collections import deque as _deque
from collections.abc import Mapping as _Mapping
from collections.abc import Sequence as _Sequence
from functools import cache as _cache
from types import NoneType as _NoneType
from types import UnionType as _UnionType

from mtchrs.matchers import Matcher as _Matcher
from mtchrs.matchers import PersistentMatcher as _PersistentMatcher
from mtchrs.matchers import _is_class

__all__ = ["any", "eq", "partial_dict", "pred", "regex", "type", "unordered"]

_TYPE_ERROR = "mtch.type() requires one or more types or unions of types"


def any() -> _Matcher:
    """Return a matcher that accepts any value."""

    return _Matcher(lambda v: True, lambda: "mtch.any()")


def eq() -> _PersistentMatcher:
    """Return a matcher that captures the first value it is compared with."""

    return _PersistentMatcher()


def type(*types: object) -> _Matcher:
    """Match instances of any supplied class or union of classes."""

    if not types:
        raise TypeError(_TYPE_ERROR)

    allowed = []
    names = []
    for candidate in types:
        origin = _t.get_origin(candidate)
        is_union = origin is _UnionType or origin is _t.Union
        members: tuple[object, ...] = (
            _t.get_args(candidate) if is_union else (candidate,)
        )
        member_names = []
        for cls in members:
            if not _is_class(cls) or cls is _t.Any:
                raise TypeError(_TYPE_ERROR)
            allowed.append(cls)
            member_names.append(
                "None" if is_union and cls is _NoneType else cls.__qualname__
            )
        names.append(" | ".join(member_names))

    classes = tuple(allowed)
    label = ", ".join(names)
    return _Matcher(lambda v: isinstance(v, classes), lambda: f"mtch.type({label})")


def regex(pattern: str | _re.Pattern[str]) -> _Matcher:
    """Match an entire string using a text regular expression."""

    compiled = _re.compile(pattern)
    if isinstance(compiled.pattern, bytes):
        raise TypeError("mtch.regex() requires a text pattern")
    return _Matcher(
        lambda v: isinstance(v, str) and compiled.fullmatch(v) is not None,
        lambda: f"mtch.regex({pattern!r})",
    )


def pred(predicate: _t.Callable[[_t.Any], object], name: str | None = None) -> _Matcher:
    """Match truthy predicate results and propagate predicate exceptions.

    Args:
        predicate: Callable returning a truthy value when the value matches.
        name: Optional representation used for ``repr``. Defaults to the
            predicate's ``__name__`` when available.
    """

    repr_str = (
        name if name is not None else getattr(predicate, "__name__", "<predicate>")
    )
    return _Matcher(lambda v: bool(predicate(v)), lambda: f"mtch.pred({repr_str})")


def partial_dict(expected: _Mapping[_t.Any, object]) -> _Matcher:
    """Match a mapping containing every expected key and value."""
    required = dict(expected)

    def matches(value: object) -> bool:
        return isinstance(value, _Mapping) and all(
            key in value and _equal(item, value[key]) for key, item in required.items()
        )

    return _Matcher(matches, lambda: f"mtch.partial_dict({required!r})")


def unordered(expected: _Sequence[object]) -> _Matcher:
    """Match a list or tuple with exactly the expected elements in any order.

    Elements may be compared with several candidates. Use side-effect-free
    comparisons and capture any persistent matchers before using them here.
    """
    items = tuple(expected)

    def matches(value: object) -> bool:
        return (
            isinstance(value, (list, tuple))
            and len(items) == len(value)
            and _has_assignment(items, value)
        )

    return _Matcher(matches, lambda: f"mtch.unordered({list(items)!r})")


def _equal(expected: object, actual: object) -> bool:
    return expected is actual or bool(expected == actual)


def _has_assignment(expected: tuple[object, ...], actual: _Sequence[object]) -> bool:
    # Index each slot independently so duplicates can each be used once.
    owner: dict[int, int] = {}

    @_cache
    def compatible(expected_index: int, actual_index: int) -> bool:
        return _equal(expected[expected_index], actual[actual_index])

    def assign(start: int) -> bool:
        # Follow occupied slots to their owners until a free slot can take
        # one of them. Then reassign the owners along that path.
        pending = _deque([start])
        previous_slot: dict[int, int | None] = {start: None}
        candidate_for: dict[int, int] = {}
        while pending:
            expected_index = pending.popleft()
            for slot in range(len(actual)):
                if slot in candidate_for or not compatible(expected_index, slot):
                    continue
                candidate_for[slot] = expected_index
                if slot in owner:
                    displaced = owner[slot]
                    previous_slot[displaced] = slot
                    pending.append(displaced)
                    continue

                target: int | None = slot
                while target is not None:
                    expected_index = candidate_for[target]
                    owner[target] = expected_index
                    target = previous_slot[expected_index]
                return True
        return False

    return all(assign(index) for index in range(len(expected)))
