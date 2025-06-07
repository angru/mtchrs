# Usage

This library exposes a simple `Matcher` class and helper constructors via the `mtch` alias.

## `mtch.any`

Matches any value.

```python
assert mtch.any() == "anything"
```

## `mtch.type`

Matches when the value is an instance of the provided type or types.

```python
assert mtch.type(int) == 1
assert mtch.type(int, float) == 3.14
```

## `mtch.regex`

Matches a string against a regular expression.

```python
assert mtch.regex(r"\d+") == "123"
```

## `mtch.eq`

Creates a persistent matcher that remembers the first value it was compared with and requires subsequent comparisons to match that value.

```python
m = mtch.eq()
assert m == "foo"
assert m == "foo"  # subsequent comparisons must match
```

## Combining matchers

Matchers support logical operators:

* `&` — logical AND
* `|` — logical OR
* `~` — logical NOT

```python
number = mtch.type(int) | (mtch.type(str) & mtch.regex(r"\d+"))
assert number == 123
assert number == "456"
```

Matchers can also be used inside dictionaries or other containers for nested comparisons.

## Nested data structures

Matchers can be mixed into lists or dictionaries to validate complex results without checking every value exactly.

```python
matcher = {
    "id": mtch.type(int),
    "items": [
        {"value": mtch.regex(r"^x"), "meta": mtch.any()},
        mtch.type(float),
    ],
}
data = {"id": 1, "items": [{"value": "xyz", "meta": {}}, 1.5]}
assert matcher == data
```

## Mock call assertions

`Matcher` instances work with `unittest.mock` and pytest helpers. They can be used to assert against `call_args` or `call_args_list` when exact values vary.

```python
from unittest.mock import Mock, call

mock = Mock()
mock("foo", {"id": 1})

expected = call(mtch.regex("f.o"), {"id": mtch.type(int)})
assert mock.call_args == expected

mock = Mock()
mock(1)
mock("bar")

expected = [call(mtch.type(int)), call(mtch.regex("ba."))]
assert mock.call_args_list == expected
```
