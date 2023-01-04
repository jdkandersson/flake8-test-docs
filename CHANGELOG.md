# Changelog

## [Unreleased]

## [v1.0.8] - 2023-01-04

### Added

- Support for flake8 version 5

## [v1.0.7] - 2022-12-29

### Fixed

- Corrected default test filename regex to `test_.*\.py` from `test_.*.py`
  which previously did not correctly escape the `.` before the extension.

## [v1.0.6] - 2022-12-28

### Fixed

- Switch to using inbuilt types rather than from `typing`

## [v1.0.5] - 2022-12-23

### Fixed

- Remove dependency on presence of `pyproject.toml` file

## [v1.0.0] - 2022-12-23

### Added

- Lint checks for test docs using the arrange/act/assert pattern
- Lint checks for longer descriptions of each stage
- `--test-docs-pattern` argument to customise the docstring pattern
- `--test-docs-filename-pattern` argument to customise the test file discovery
- `--test-docs-function-pattern` argument to customise the test function
  discovery
- support for flake8 `--indent-size` argument

[//]: # "Release links"
[v1.0.0]: https://github.com/jdkandersson/flake8-test-docs/releases/v1.0.0
[v1.0.5]: https://github.com/jdkandersson/flake8-test-docs/releases/v1.0.5
[v1.0.6]: https://github.com/jdkandersson/flake8-test-docs/releases/v1.0.6
[v1.0.7]: https://github.com/jdkandersson/flake8-test-docs/releases/v1.0.7
[v1.0.8]: https://github.com/jdkandersson/flake8-test-docs/releases/v1.0.8
