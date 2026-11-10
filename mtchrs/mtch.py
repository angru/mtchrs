"""Factory functions for composable equality matchers."""

import re
import typing as t
from collections import deque
from collections.abc import Mapping, Sequence
from functools import cache
from types import NoneType, UnionType

from mtchrs.matchers import Matcher, PersistentMatcher, _is_class

__all__ = ["any", "eq", "partial_dict", "pred", "regex", "type", "unordered"]

_TYPE_ERROR = "mtch.type() requires one or more types or unions of types"


def any() -> Matcher:
    """Return a matcher that accepts any value."""

    return Matcher(lambda v: True, lambda: "mtch.any()")


def eq() -> PersistentMatcher:
    """Return a matcher that captures the first value it is compared with."""

    return PersistentMatcher()


def type(*types: object) -> Matcher:
    """Match instances of any supplied class or union of classes."""

    if not types:
        raise TypeError(_TYPE_ERROR)

    allowed = []
    names = []
    for candidate in types:
        origin = t.get_origin(candidate)
        is_union = origin is UnionType or origin is t.Union
        members: tuple[object, ...] = (
            t.get_args(candidate) if is_union else (candidate,)
        )
        member_names = []
        for cls in members:
            if not _is_class(cls) or cls is t.Any:
                raise TypeError(_TYPE_ERROR)
            allowed.append(cls)
            member_names.append(
                "None" if is_union and cls is NoneType else cls.__qualname__
            )
        names.append(" | ".join(member_names))

    classes = tuple(allowed)
    label = ", ".join(names)
    return Matcher(lambda v: isinstance(v, classes), lambda: f"mtch.type({label})")


def regex(pattern: str | re.Pattern[str]) -> Matcher:
    """Match an entire string using a text regular expression."""

    compiled = re.compile(pattern)
    if isinstance(compiled.pattern, bytes):
        raise TypeError("mtch.regex() requires a text pattern")
    return Matcher(
        lambda v: isinstance(v, str) and compiled.fullmatch(v) is not None,
        lambda: f"mtch.regex({pattern!r})",
    )


def pred(predicate: t.Callable[[t.Any], object], name: str | None = None) -> Matcher:
    """Match truthy predicate results and propagate predicate exceptions.

    Args:
        predicate: Callable returning a truthy value when the value matches.
        name: Optional representation used for ``repr``. Defaults to the
            predicate's ``__name__`` when available.
    """

    repr_str = (
        name if name is not None else getattr(predicate, "__name__", "<predicate>")
    )
    return Matcher(lambda v: bool(predicate(v)), lambda: f"mtch.pred({repr_str})")


def partial_dict(expected: Mapping[t.Any, object]) -> Matcher:
    """Match a mapping containing every expected key and value."""
    required = dict(expected)

    def matches(value: object) -> bool:
        return isinstance(value, Mapping) and all(
            key in value and _equal(item, value[key]) for key, item in required.items()
        )

    return Matcher(matches, lambda: f"mtch.partial_dict({required!r})")


def unordered(expected: Sequence[object]) -> Matcher:
    """Match a list with exactly the expected elements in any order.

    Elements may be compared with several candidates. Use side-effect-free
    comparisons and capture any persistent matchers before using them here.
    """
    items = tuple(expected)

    def matches(value: object) -> bool:
        return (
            isinstance(value, list)
            and len(items) == len(value)
            and _has_assignment(items, value)
        )

    return Matcher(matches, lambda: f"mtch.unordered({list(items)!r})")


def _equal(expected: object, actual: object) -> bool:
    return expected is actual or bool(expected == actual)


def _has_assignment(expected: tuple[object, ...], actual: list[object]) -> bool:
    # Index each slot independently so duplicates can each be used once.
    owner: dict[int, int] = {}

    @cache
    def compatible(expected_index: int, actual_index: int) -> bool:
        return _equal(expected[expected_index], actual[actual_index])

    def assign(start: int) -> bool:
        # Follow occupied slots to their owners until a free slot can take
        # one of them. Then reassign the owners along that path.
        pending = deque([start])
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
