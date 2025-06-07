"""Composable matchers for flexible equality assertions.

The :class:`Matcher` class wraps a predicate used during ``==`` comparisons.
Matchers can be combined with ``&`` and ``|`` for logical composition and
inverted with ``~``. They work inside nested data structures and integrate with
``unittest.mock`` for verifying mock calls.
"""

from __future__ import annotations

import re
import typing as t


class Matcher:
    """Base class for value matchers.

    ``Matcher`` objects wrap a predicate function used during ``==``
    comparisons. They can be combined with ``&`` and ``|`` to build complex
    conditions or inverted with ``~``.
    """

    def __init__(self, func: t.Callable[[t.Any], bool], repr_func: t.Callable[[], str]):
        self._func = func
        self._repr_func = repr_func

    def __eq__(self, other: t.Any) -> bool:
        return self._func(other)

    def __and__(self, other: Matcher) -> Matcher:
        return Matcher(
            lambda v: self == v and other == v,
            lambda: f"({self}) & ({other})",
        )

    def __or__(self, other: "Matcher") -> "Matcher":
        return Matcher(
            lambda v: self == v or other == v,
            lambda: f"({self}) | ({other})",
        )

    def __repr__(self) -> str:
        return self._repr_func()

    def __invert__(self) -> Matcher:
        return Matcher(lambda v: not self._func(v), lambda: f"~({self})")

    @staticmethod
    def any() -> Matcher:
        """Return a matcher that accepts any value."""

        return Matcher(lambda v: True, lambda: "Any")

    @staticmethod
    def eq() -> PersistentMatcher:
        """Return a matcher that remembers the first value it matches."""

        return PersistentMatcher()

    @staticmethod
    def type(*types: type) -> Matcher:
        """Match when ``value`` is an instance of ``types``."""

        return Matcher(
            lambda v: isinstance(v, types),
            lambda: f'Type[{" | ".join((str(t) for t in types))}]',
        )

    @staticmethod
    def regex(pattern: t.Union[str, re.Pattern]) -> Matcher:
        """Match a string using ``pattern``."""

        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        return Matcher(
            lambda v: isinstance(v, str) and bool(compiled.match(v)),
            lambda: f"{compiled}",
        )

    @staticmethod
    def pred(predicate: t.Callable[[t.Any], bool], name: str | None = None) -> Matcher:
        """Create a matcher from a custom predicate.

        Args:
            predicate: Callable returning ``True`` when the value matches.
            name: Optional representation used for ``repr``. Defaults to the
                predicate's ``__name__`` when available.
        """

        repr_str = (
            name if name is not None else getattr(predicate, "__name__", "<predicate>")
        )
        return Matcher(predicate, lambda: f"pred({repr_str})")


class PersistentMatcher(Matcher):
    """Matcher that stores the first value it matches for future comparisons."""

    _no_value = object()

    def __init__(self):
        self._value = self._no_value
        super().__init__(
            self._func, lambda: f"PersistentMatcher(value={self._value!r})"
        )

    def _func(self, other: t.Any) -> bool:
        if self._value is self._no_value:
            self._value = other
        return self._value == other


mtch = Matcher
