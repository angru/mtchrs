# mtchrs

[![build](https://github.com/angru/mtchrs/actions/workflows/lint-and-test.yml/badge.svg)](https://github.com/angru/mtchrs/actions/workflows/lint-and-test.yml)
[![codecov](https://codecov.io/gh/angru/mtchrs/graph/badge.svg?token=HWB0SS88F0)](https://codecov.io/gh/angru/mtchrs)

`mtchrs` provides composable matchers that can be nested inside any data structure. Use them in tests where values like database IDs or UUIDs change between runs. Matchers also integrate with `unittest.mock` assertions such as `call_args_list` for verifying mock calls.

The persistent matcher `mtch.eq()` is especially handy for tracking values that must stay identical across nested results or several steps of a workflow.

## Installation

```bash
pip install mtchrs
```

## Example

```python
from mtchrs.matchers import mtch

data = {"id": 1, "items": ["xyz", 1.5]}
matcher = {"id": mtch.type(int), "items": [mtch.regex(r"^x"), mtch.type(float)]}
assert matcher == data
```

## Contributing

Pull requests are welcome! Install dependencies from the `dev`, `lint` and `test` groups using [uv](https://github.com/astral-sh/uv) and run the linters and test suite before submitting a PR:

```bash
uv pip install -e .[dev,lint,test]
uv run pre-commit run --all-files
uv run pytest
```

## License

This project is licensed under the MIT License.

### Documentation
See the [documentation](https://angru.github.io/mtchrs/) for more details.
