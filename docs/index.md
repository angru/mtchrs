# mtchrs

`mtchrs` provides small, composable matchers for validating values in tests and data structures. It is particularly useful when your code returns values that change from run to run, such as database generated IDs or UUIDs. Matchers can be nested inside dictionaries or lists and even used in `unittest.mock` assertions.

## Installation

```bash
pip install mtchrs
```

## Quickstart

```python
from mtchrs import mtch

assert mtch.any() == 123
assert mtch.type(int) == 42
assert mtch.regex(r"\d+") == "456"
assert mtch.pred(lambda v: v > 0, "positive") == 1

id_matcher = mtch.eq()
assert {"id": 1, "child": {"id": 1}} == {"id": id_matcher, "child": {"id": id_matcher}}
```

`mtch.eq()` remembers the first value it matches, making it ideal for verifying
repeated IDs or tokens that must remain the same across a complex result or a
series of operations.

See the [Usage](usage.md) page for details on available matchers.
