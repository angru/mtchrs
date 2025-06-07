from unittest.mock import Mock, call


from mtchrs.matchers import mtch


def test_basic_matchers() -> None:
    assert mtch.any() == "anything"
    assert mtch.type(int, float) == 3.14
    assert mtch.regex(r"\d+") == "42"


def test_logical_operators_and_invert() -> None:
    number = mtch.type(int) | (mtch.type(str) & mtch.regex(r"\d+"))
    assert number == 789
    assert number == "789"
    assert ~mtch.type(int) == "foo"
    assert ~(mtch.type(int) & mtch.regex(r"\d+")) == 1


def test_nested_data_structures() -> None:
    matcher = {
        "id": mtch.type(int),
        "items": [
            {"value": mtch.regex(r"^x"), "meta": mtch.any()},
            mtch.type(float),
        ],
    }
    data = {"id": 1, "items": [{"value": "xyz", "meta": {}}, 1.5]}
    assert matcher == data


def test_persistent_matcher_keeps_value() -> None:
    user_id = mtch.eq()
    assert {"id": 1, "child": {"id": 2}} != {"id": user_id, "child": {"id": user_id}}
    assert {"id": 1, "child": {"id": 1}} == {"id": user_id, "child": {"id": user_id}}


def test_dynamic_repr_with_persistent_matcher() -> None:
    persistent = mtch.eq()
    matcher = mtch.type(int) & persistent

    assert matcher == 7
    assert repr(matcher) == "(Type[<class 'int'>]) & (PersistentMatcher(value=7))"

    inverted = ~persistent
    assert repr(inverted) == "~(PersistentMatcher(value=7))"


def test_persistent_matcher_repr() -> None:
    matcher = mtch.eq()
    assert matcher == "foo"
    assert repr(matcher) == "PersistentMatcher(value='foo')"


def test_matchers_in_mock_call_args() -> None:
    mock = Mock()
    mock("foo", {"id": 1})

    expected = call(mtch.regex("f.o"), {"id": mtch.type(int)})
    assert mock.call_args == expected


def test_call_args_list_with_matchers() -> None:
    mock = Mock()
    mock(1)
    mock("bar")

    expected = [call(mtch.type(int)), call(mtch.regex("ba."))]
    assert mock.call_args_list == expected
