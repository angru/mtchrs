"""Composable matchers for flexible equality assertions.

The :class:`Matcher` class wraps a predicate used during ``==`` comparisons.
Matchers can be combined with ``&`` and ``|`` for logical composition and
inverted with ``~``. They work inside nested data structures and integrate with
``unittest.mock`` for verifying mock calls.
"""

from __future__ import annotations

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

    def _compare(self, other: object) -> bool:
        if self._value is self._no_value:
            self._value = other
        return bool(self._value == other)

    def _capture_repr(self) -> str:
        if self._value is self._no_value:
            return "mtch.eq()"
        return f"mtch.eq({self._value!r})"


def _is_class(value: object) -> t.TypeGuard[type]:
    # Python 3.10 generic aliases can appear to be classes via __class__.
    return issubclass(type(value), type)


def _as_matcher(expected: object) -> Matcher:
    if isinstance(expected, Matcher):
        return expected
    if _is_class(expected):
        raise TypeError("Use mtch.type(...) to combine matchers with a class")
    return Matcher(lambda value: expected == value, lambda: repr(expected))
