# Changelog

## [Unreleased]

## [v1.0.2] - 2022-12-23

- Fix missing toml dependency for Python 3.10 and earlier

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
[v1.0.2]: https://github.com/jdkandersson/flake8-test-docs/releases/v1.0.2
