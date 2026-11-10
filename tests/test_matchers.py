import operator
import re
from collections import UserDict
from collections.abc import Callable
from types import ModuleType
from typing import Optional
from unittest.mock import Mock, call

import pytest

from mtchrs import Matcher, PersistentMatcher, mtch


def test_factory_namespace() -> None:
    from mtchrs.mtch import any as any_matcher

    assert isinstance(mtch, ModuleType)
    assert mtch.any is any_matcher
    assert isinstance(mtch.any(), Matcher)
    assert isinstance(mtch.eq(), PersistentMatcher)
    assert not hasattr(Matcher, "any")


class TestAnyMatcher:
    def test_matches_any_value(self) -> None:
        matcher = mtch.any()
        assert matcher == "foo"
        assert matcher == 123

    def test_repr(self) -> None:
        assert repr(mtch.any()) == "mtch.any()"


class TestTypeMatcher:
    def test_matches_allowed_types(self) -> None:
        assert mtch.type(int) == 1
        assert mtch.type(int, float) == 3.14

    def test_does_not_match_wrong_type(self) -> None:
        assert mtch.type(str) != 1

    def test_repr(self) -> None:
        assert repr(mtch.type(int)) == "mtch.type(int)"
        assert repr(mtch.type(int, float)) == "mtch.type(int, float)"

    @pytest.mark.parametrize("types", [(), (int, "str"), (int | list[int],)])
    def test_rejects_invalid_arguments(self, types: tuple[object, ...]) -> None:
        with pytest.raises(TypeError, match="requires one or more types"):
            mtch.type(*types)

    @pytest.mark.parametrize("union", [int | None, Optional[int]])  # noqa: UP045
    def test_matches_unions(self, union: object) -> None:
        matcher = mtch.type(union, float)
        assert matcher == 1
        missing = None
        assert matcher == missing
        assert matcher == 1.5
        assert matcher != "1"
        assert repr(matcher) == "mtch.type(int | None, float)"


class TestRegexMatcher:
    def test_matches_pattern(self) -> None:
        assert mtch.regex(r"\d+") == "42"

    def test_does_not_match_pattern(self) -> None:
        assert mtch.regex(r"\d+") != "foo"

    def test_matches_entire_string(self) -> None:
        assert mtch.regex(r"\d+") != "42abc"
        assert mtch.regex(r"\d+") != 42
        assert mtch.regex(r"\d+.*") == "42abc"

    def test_compiled_pattern_preserves_flags(self) -> None:
        matcher = mtch.regex(re.compile("abc", re.IGNORECASE))
        assert matcher == "ABC"
        assert matcher != "ABCD"
        assert repr(matcher) == "mtch.regex(re.compile('abc', re.IGNORECASE))"

    @pytest.mark.parametrize("pattern", [b"abc", re.compile(b"abc")])
    def test_rejects_bytes_patterns(self, pattern: bytes | re.Pattern[bytes]) -> None:
        with pytest.raises(TypeError, match="requires a text pattern"):
            mtch.regex(pattern)  # type: ignore[arg-type]

    def test_repr(self) -> None:
        assert repr(mtch.regex("abc")) == "mtch.regex('abc')"


class TestPredicateMatcher:
    def test_matches_when_true(self) -> None:
        def is_even(value: int) -> bool:
            return value % 2 == 0

        assert mtch.pred(is_even) == 2

    def test_matches_lambda_predicate(self) -> None:
        matcher = mtch.pred(lambda v: v % 2 == 0)
        assert matcher == 4

    def test_does_not_match_when_false(self) -> None:
        assert mtch.pred(lambda v: v > 0) != -1

    def test_repr(self) -> None:
        def is_even(value: int) -> bool:
            return value % 2 == 0

        assert repr(mtch.pred(is_even)) == "mtch.pred(is_even)"

    def test_lambda_repr(self) -> None:
        matcher = mtch.pred(lambda v: True)
        assert repr(matcher) == "mtch.pred(<lambda>)"

    def test_predicate_result_is_a_bool(self) -> None:
        matcher = mtch.pred(lambda v: v)
        assert (matcher == 3) is True
        assert (matcher == 0) is False

    def test_predicate_exception_propagates(self) -> None:
        with pytest.raises(TypeError):
            _ = mtch.pred(lambda v: v > 0) == "foo"


class TestPersistentMatcher:
    def test_keeps_value_across_comparisons(self) -> None:
        user_id = mtch.eq()
        bad = {"id": 1, "child": {"id": 2}}
        good = {"id": 1, "child": {"id": 1}}
        assert bad != {"id": user_id, "child": {"id": user_id}}
        assert good == {"id": user_id, "child": {"id": user_id}}

    def test_value_and_repr_before_capture(self) -> None:
        matcher = mtch.eq()
        assert repr(matcher) == "mtch.eq()"
        with pytest.raises(ValueError, match="has not captured"):
            _ = matcher.value

    def test_value_is_read_only(self) -> None:
        matcher = mtch.eq()
        missing = None
        assert matcher == missing
        assert matcher.value is None
        with pytest.raises(AttributeError):
            matcher.value = 1  # type: ignore[misc]

    def test_failed_enclosing_match_still_captures(self) -> None:
        matcher = mtch.eq()
        assert (matcher & mtch.type(int)) != "foo"
        assert matcher.value == "foo"

    def test_repr_after_matching(self) -> None:
        matcher = mtch.eq()
        assert matcher == "foo"
        assert repr(matcher) == "mtch.eq('foo')"

    def test_dynamic_repr_with_logical_ops(self) -> None:
        persistent = mtch.eq()
        matcher = mtch.type(int) & persistent
        assert matcher == 7
        assert repr(matcher) == "mtch.type(int) & mtch.eq(7)"
        inverted = ~persistent
        assert repr(inverted) == "~mtch.eq(7)"


class TestLogicalOperators:
    def test_and_or_not(self) -> None:
        number = mtch.type(int) | (mtch.type(str) & mtch.regex(r"\d+"))
        assert number == 789
        assert number == "789"
        assert ~mtch.type(int) == "foo"
        assert ~(mtch.type(int) & mtch.regex(r"\d+")) == 1

    def test_repr_preserves_grouping(self) -> None:
        matcher = (mtch.type(int) | mtch.type(str)) & ~mtch.regex("abc")
        assert repr(matcher) == "(mtch.type(int) | mtch.type(str)) & ~mtch.regex('abc')"
        assert (
            repr(~matcher)
            == "~((mtch.type(int) | mtch.type(str)) & ~mtch.regex('abc'))"
        )

    def test_or_with_literal_in_both_orders(self) -> None:
        missing = None
        for matcher in (mtch.type(int) | missing, missing | mtch.type(int)):
            assert matcher == missing
            assert matcher == 7
            assert matcher != "foo"

    def test_reflected_operators_short_circuit_left_to_right(self) -> None:
        missing = None
        capture = mtch.eq()
        assert (missing | capture) == missing
        assert (missing & capture) != 7
        with pytest.raises(ValueError):
            _ = capture.value

        assert (7 & capture) == 7
        assert capture.value == 7
        assert repr(7 & capture) == "7 & mtch.eq(7)"

    @pytest.mark.parametrize("combine", [operator.and_, operator.or_])
    def test_rejects_bare_class_operands(
        self, combine: Callable[[object, object], object]
    ) -> None:
        with pytest.raises(TypeError, match=r"mtch\.type"):
            combine(mtch.any(), int)
        with pytest.raises(TypeError, match=r"mtch\.type"):
            combine(int, mtch.any())


class TestPartialDictMatcher:
    def test_matches_required_values_in_a_mapping(self) -> None:
        matcher = mtch.partial_dict({1: mtch.type(int), "active": None})
        assert UserDict({1: 42, "active": None, "extra": True}) == matcher
        assert matcher != {1: 42}
        assert matcher != {1: "42", "active": None}
        assert matcher != [(1, 42), ("active", None)]

    def test_empty_expectation_still_requires_a_mapping(self) -> None:
        assert mtch.partial_dict({}) == {"extra": True}
        assert mtch.partial_dict({}) != []

    def test_repr(self) -> None:
        assert repr(mtch.partial_dict({"id": mtch.type(int)})) == (
            "mtch.partial_dict({'id': mtch.type(int)})"
        )


class TestUnorderedMatcher:
    def test_assigns_overlapping_matchers(self) -> None:
        matcher = mtch.unordered([mtch.any(), mtch.type(int), 1])
        assert [1, 2, "x"] == matcher
        assert matcher == [1, "x", 2]
        assert matcher != [1, "x", "y"]

    def test_counts_duplicates_and_supports_unhashable_values(self) -> None:
        matcher = mtch.unordered([{"id": 1}, [2], [2]])
        assert matcher == [[2], {"id": 1}, [2]]
        assert matcher != [[2], {"id": 1}, {"id": 1}]
        assert matcher != [{"id": 1}, [2]]
        assert matcher != [{"id": 1}, [2], [2], [2]]

    def test_empty_expectation_still_requires_a_list(self) -> None:
        assert mtch.unordered([]) == []
        assert mtch.unordered([]) != ()

    def test_uses_an_already_captured_value(self) -> None:
        user_id = mtch.eq()
        assert user_id == 7
        matcher = mtch.unordered([mtch.partial_dict({"id": user_id}), {"id": 2}])
        assert matcher == [{"id": 2}, {"id": 7, "name": "Ada"}]
        assert matcher != [{"id": 2}, {"id": 8, "name": "Ada"}]
        assert user_id.value == 7

    def test_repr(self) -> None:
        assert (
            repr(mtch.unordered([mtch.any(), 1])) == "mtch.unordered([mtch.any(), 1])"
        )


class TestNestedStructures:
    def test_nested_data_structures(self) -> None:
        matcher = {
            "id": mtch.type(int),
            "items": [
                {"value": mtch.regex(r"x.*"), "meta": mtch.any()},
                mtch.type(float),
            ],
        }
        data = {"id": 1, "items": [{"value": "xyz", "meta": {}}, 1.5]}
        assert matcher == data


class TestMockIntegration:
    def test_matchers_in_mock_call_args(self) -> None:
        mock = Mock()
        mock("foo", {"id": 1})

        expected = call(mtch.regex("f.o"), {"id": mtch.type(int)})
        assert mock.call_args == expected

    def test_call_args_list_with_matchers(self) -> None:
        mock = Mock()
        mock(1)
        mock("bar")

        expected = [call(mtch.type(int)), call(mtch.regex("ba."))]
        assert mock.call_args_list == expected
