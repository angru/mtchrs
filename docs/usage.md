# Usage

Import the `mtch` module with `from mtchrs import mtch`. Its factories return
`Matcher` instances that you can compare or combine.

## `mtch.any`

Matches any value.

```python
assert mtch.any() == "anything"
```

## `mtch.type`

Matches values that are instances of any of the supplied classes or unions.
Supply at least one class or union of classes.

```python
assert mtch.type(int) == 1
assert mtch.type(int, float) == 3.14
missing = None
assert mtch.type(int | None) == missing
```

## `mtch.regex`

Matches an entire string using a text pattern or a compiled text regular expression.
Add `.*` after the pattern to allow trailing characters. Bytes patterns raise
`TypeError` when the matcher is constructed.

```python
assert mtch.regex(r"\d+") == "123"
assert mtch.regex(r"\d+") != "123abc"
assert mtch.regex(r"\d+.*") == "123abc"
```

## `mtch.pred`

Creates a matcher from a custom predicate. Its result is converted to `bool`.
Exceptions raised by the predicate propagate to the caller. Use a type guard
such as `mtch.type(int) & mtch.pred(is_even)` when a predicate expects integers.

```python
def is_even(value: int) -> bool:
    return value % 2 == 0

assert mtch.pred(is_even) == 2
assert mtch.pred(lambda v: v > 0, "positive") == 3
```

## `mtch.eq`

Creates a persistent matcher that remembers the first value it was compared with and requires subsequent comparisons to match that value.

```python
m = mtch.eq()
assert m == "foo"
assert m == "foo"  # subsequent comparisons must match
assert m.value == "foo"
```

The read-only `.value` property raises `ValueError` before the first comparison.
For example, in `(mtch.eq() & mtch.type(int)) == "x"`, the first comparison
captures `"x"` before the type check rejects it. For searches with `in`,
`assert_any_call`, or `assert_has_calls`, compare the matcher explicitly with the
intended value first.

Persistent matchers shine when you need to assert that the *same* value appears
multiple times. Some handy scenarios include:

* **Repeated identifiers in nested objects** – capture an ID once and ensure it
  matches everywhere else in the response.
* **Tokens shared across multi-step operations** – store a session token from
  one request and verify it is reused in later calls.
* **Mock call sequences** – check that the exact argument value is passed to
  different functions or multiple calls of the same mock.

For example:

```python
from unittest.mock import Mock, call

user_id = mtch.eq()
assert {"id": 1, "child": {"id": 1}} == {"id": user_id, "child": {"id": user_id}}

token = mtch.eq()
assert {"token": "abc"} == {"token": token}
assert {"auth": "abc"} == {"auth": token}

mock = Mock()
mock(1)
mock(1)
assert mock.call_args_list == [call(user_id), call(user_id)]

bad = {"id": 1, "child": {"id": 2}}
assert bad != {"id": user_id, "child": {"id": user_id}}
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

You can also combine a matcher with a literal on either side. Operators evaluate
the left operand first and short-circuit as needed. Wrap classes with
`mtch.type(...)` before using them as operands.

```python
optional_int = None | mtch.type(int)
missing = None
assert optional_int == missing
assert optional_int == 7
```

Matchers can also be used inside dictionaries or other containers for nested comparisons.

## Nested data structures

Matchers can be mixed into lists or dictionaries to validate complex results without checking every value exactly.

```python
matcher = {
    "id": mtch.type(int),
    "items": [
        {"value": mtch.regex(r"x.*"), "meta": mtch.any()},
        mtch.type(float),
    ],
}
data = {"id": 1, "items": [{"value": "xyz", "meta": {}}, 1.5]}
assert matcher == data
```

## `mtch.partial_dict`

Matches a mapping that contains each specified key and value. Extra keys are
allowed. A required key must be present even when its expected value is `None`.

```python
user = mtch.partial_dict({"id": mtch.type(int), "deleted_at": None})
assert {"id": 7, "name": "Ada", "deleted_at": None} == user
assert {"id": 7, "name": "Ada"} != user
```

## `mtch.unordered`

Matches a list with exactly the expected elements in any order. Each expected
element must match a distinct list position, so duplicates count separately.

```python
assert mtch.unordered([mtch.type(int), 1]) == [1, 2]
assert mtch.unordered([[1], [2], [2]]) == [[2], [1], [2]]
```

An expected element may be compared with several candidates. Use
side-effect-free predicates, and compare any `eq()` matcher explicitly with its
intended value before using it inside `unordered`.

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

## Gotchas

- `mtch.type(int)` also matches `True` and `False` because `bool` is a subclass of `int`.
- Matchers are unhashable. Use them as dictionary values or list elements.
- A custom value's `__eq__` may return `False` without giving the matcher a
  chance to compare. Put the matcher on the left for those values.
