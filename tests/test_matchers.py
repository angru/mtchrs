from unittest.mock import Mock, call

from mtchrs import mtch


class TestAnyMatcher:
    def test_matches_any_value(self) -> None:
        matcher = mtch.any()
        assert matcher == "foo"
        assert matcher == 123

    def test_repr(self) -> None:
        assert repr(mtch.any()) == "Any"


class TestTypeMatcher:
    def test_matches_allowed_types(self) -> None:
        assert mtch.type(int) == 1
        assert mtch.type(int, float) == 3.14

    def test_does_not_match_wrong_type(self) -> None:
        assert mtch.type(str) != 1

    def test_repr(self) -> None:
        assert repr(mtch.type(int)) == "Type[<class 'int'>]"
        assert repr(mtch.type(int, float)) == "Type[<class 'int'> | <class 'float'>]"


class TestRegexMatcher:
    def test_matches_pattern(self) -> None:
        assert mtch.regex(r"\d+") == "42"

    def test_does_not_match_pattern(self) -> None:
        assert mtch.regex(r"\d+") != "foo"

    def test_repr(self) -> None:
        assert repr(mtch.regex(r"\d+")) == "re.compile('\\\\d+')"


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

        assert repr(mtch.pred(is_even)) == "pred(is_even)"

    def test_lambda_repr(self) -> None:
        matcher = mtch.pred(lambda v: True)
        assert repr(matcher) == "pred(<lambda>)"


class TestPersistentMatcher:
    def test_keeps_value_across_comparisons(self) -> None:
        user_id = mtch.eq()
        bad = {"id": 1, "child": {"id": 2}}
        good = {"id": 1, "child": {"id": 1}}
        assert bad != {"id": user_id, "child": {"id": user_id}}
        assert good == {"id": user_id, "child": {"id": user_id}}

    def test_repr_after_matching(self) -> None:
        matcher = mtch.eq()
        assert matcher == "foo"
        assert repr(matcher) == "PersistentMatcher(value='foo')"

    def test_dynamic_repr_with_logical_ops(self) -> None:
        persistent = mtch.eq()
        matcher = mtch.type(int) & persistent
        assert matcher == 7
        assert repr(matcher) == "(Type[<class 'int'>]) & (PersistentMatcher(value=7))"
        inverted = ~persistent
        assert repr(inverted) == "~(PersistentMatcher(value=7))"


class TestLogicalOperators:
    def test_and_or_not(self) -> None:
        number = mtch.type(int) | (mtch.type(str) & mtch.regex(r"\d+"))
        assert number == 789
        assert number == "789"
        assert ~mtch.type(int) == "foo"
        assert ~(mtch.type(int) & mtch.regex(r"\d+")) == 1


class TestNestedStructures:
    def test_nested_data_structures(self) -> None:
        matcher = {
            "id": mtch.type(int),
            "items": [
                {"value": mtch.regex(r"^x"), "meta": mtch.any()},
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
