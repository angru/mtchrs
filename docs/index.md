# mtchrs

`mtchrs` provides small, composable matchers for validating values in tests and data structures.

## Installation

```bash
pip install mtchrs
```

## Quickstart

```python
from mtchrs.matchers import mtch

assert mtch.any() == 123
assert mtch.type(int) == 42
assert mtch.regex(r"\d+") == "456"

id_matcher = mtch.eq()
assert {"id": 1, "child": {"id": 1}} == {"id": id_matcher, "child": {"id": id_matcher}}
```

See the [Usage](usage.md) page for details on available matchers.
