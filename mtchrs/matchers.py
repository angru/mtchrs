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

    _precedence = 4

    def __init__(self, func: t.Callable[[t.Any], bool], repr_func: t.Callable[[], str]):
        self._func = func
        self._repr_func = repr_func

    def __eq__(self, other: object) -> bool:
        return self._func(other)

    def __and__(self, other: object) -> Matcher:
        right = _as_matcher(other)
        result = Matcher(
            lambda v: self == v and right == v,
            lambda: f"{self._operand_repr(2)} & {right._operand_repr(2)}",
        )
        result._precedence = 2
        return result

    def __rand__(self, other: object) -> Matcher:
        return Matcher.__and__(_as_matcher(other), self)

    def __or__(self, other: object) -> Matcher:
        right = _as_matcher(other)
        result = Matcher(
            lambda v: self == v or right == v,
            lambda: f"{self._operand_repr(1)} | {right._operand_repr(1)}",
        )
        result._precedence = 1
        return result

    def __ror__(self, other: object) -> Matcher:
        return Matcher.__or__(_as_matcher(other), self)

    def __repr__(self) -> str:
        return self._repr_func()

    def __invert__(self) -> Matcher:
        return Matcher(lambda v: not self._func(v), lambda: f"~{self._operand_repr(3)}")

    def _operand_repr(self, precedence: int) -> str:
        return f"({self!r})" if self._precedence < precedence else repr(self)

    @staticmethod
    def any() -> Matcher:
        """Return a matcher that accepts any value."""

        return Matcher(lambda v: True, lambda: "mtch.any()")

    @staticmethod
    def eq() -> PersistentMatcher:
        """Return a matcher that captures the first value it is compared with."""

        return PersistentMatcher()

    @staticmethod
    def type(*types: type) -> Matcher:
        """Match when ``value`` is an instance of ``types``."""

        if not types or not all(isinstance(cls, type) for cls in types):
            raise TypeError("mtch.type() requires one or more types")
        names = ", ".join(cls.__qualname__ for cls in types)
        return Matcher(lambda v: isinstance(v, types), lambda: f"mtch.type({names})")

    @staticmethod
    def regex(pattern: str | re.Pattern[str]) -> Matcher:
        """Match an entire string using a text regular expression."""

        compiled = re.compile(pattern)
        if isinstance(compiled.pattern, bytes):
            raise TypeError("mtch.regex() requires a text pattern")
        return Matcher(
            lambda v: isinstance(v, str) and compiled.fullmatch(v) is not None,
            lambda: f"mtch.regex({pattern!r})",
        )

    @staticmethod
    def pred(
        predicate: t.Callable[[t.Any], object], name: str | None = None
    ) -> Matcher:
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


class PersistentMatcher(Matcher):
    """Matcher that stores the first value it is compared with."""

    _no_value = object()

    def __init__(self) -> None:
        self._value = self._no_value
        super().__init__(self._compare, self._capture_repr)

    @property
    def value(self) -> t.Any:
        """Return the captured value or raise ValueError before capture."""
        if self._value is self._no_value:
            raise ValueError("mtch.eq() has not captured a value yet")
        return self._value

    def _compare(self, other: t.Any) -> bool:
        if self._value is self._no_value:
            self._value = other
        return self._value == other

    def _capture_repr(self) -> str:
        if self._value is self._no_value:
            return "mtch.eq()"
        return f"mtch.eq({self._value!r})"


def _as_matcher(expected: object) -> Matcher:
    if isinstance(expected, Matcher):
        return expected
    return Matcher(lambda value: expected == value, lambda: repr(expected))


mtch = Matcher
