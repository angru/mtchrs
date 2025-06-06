from mtchrs.matchers import mtch


def test_matcher() -> None:
    assert mtch.any() == 123
    assert mtch.type(int, float) == 3.14
    assert mtch.regex(r"\d+") == "456"
    assert mtch.type(int) | (mtch.type(str) & mtch.regex(r"\d+")) == 789
    assert mtch.type(int) | (mtch.type(str) & mtch.regex(r"\d+")) == "789"

    assert {"id": mtch.type(int), "child": {"id": mtch.any()}} == {
        "id": 1,
        "child": {"id": 2},
    }


def test_matcher_keeps_value() -> None:
    user_id = mtch.eq()
    assert {"id": 1, "child": {"id": 2}} != {"id": user_id, "child": {"id": user_id}}
    assert {"id": 1, "child": {"id": 1}} == {"id": user_id, "child": {"id": user_id}}


def test_persistent_matcher_repr() -> None:
    matcher = mtch.eq()
    assert matcher == "foo"
    assert repr(matcher) == "PersistentMatcher(value='foo')"
