# mtchrs

[![build](https://github.com/angru/mtchrs/actions/workflows/lint-and-test.yml/badge.svg)](https://github.com/angru/mtchrs/actions/workflows/lint-and-test.yml)
[![codecov](https://codecov.io/gh/angru/mtchrs/graph/badge.svg?token=HWB0SS88F0)](https://codecov.io/gh/angru/mtchrs)

`mtchrs` provides composable matchers that can be nested inside any data structure. Use them in tests where values like database IDs or UUIDs change between runs. Matchers also integrate with `unittest.mock` assertions such as `call_args_list` for verifying mock calls.

### Documentation
See the [documentation](https://angru.github.io/mtchrs/) for more details.
