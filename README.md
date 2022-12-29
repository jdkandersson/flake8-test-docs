# flake8-test-docs

Have you ever needed to understand a new project and started reading the tests
only to find that you have no idea what the tests are doing? Good test
documentation is critical during test definition and when reviewing tests
written in the past or by someone else. This linter checks that the test
function docstring includes a description of the test setup, execution and
checks.

## Getting Started

```shell
python -m venv venv
source ./venv/bin/activate
pip install flake8 flake8-test-docs
flake8 test_source.py
```

On the following code:

```Python
# test_source.py
def test_foo():
    value = foo()
    assert value == "bar"
```

This will produce warnings such as:

```shell
flake8 test_source.py
test_source.py:2:1: TDO001 Docstring not defined on test function, more information: https://github.com/jdkandersson/flake8-test-docs#fix-tdo001
```

This can be resolved by changing the code to:

```Python
# test_source.py
def test_foo():
    """
    arrange: given foo that returns bar
    act: when foo is called
    assert: then bar is returned
    """
    value = foo()
    assert value == "bar"
```

## Configuration

The plugin adds the following configurations to `flake8`:

* `--test-docs-patter`: The pattern the test documentation should follow,
  e.g., `given/when/then`. Defaults to `arrange/act/assert`.
* `--test-docs-filename-pattern`: The filename pattern for test files. Defaults
  to `test_.*\.py`.
* `--test-docs-function-pattern`: The function pattern for test functions.
  Defaults to `test_.*`.


## Rules

A few rules have been defined to allow for selective suppression:

* `TDO001`: checks that test functions have a docstring.
* `TDO002`: checks that test function docstrings follow the documentation
  pattern.

### Fix TDO001

This linting rule is triggered by a test function in a test file without a
docstring. For example:

```Python
# test_source.py
def test_foo():
    result = foo()
    assert result == "bar"
```

This example can be fixed by:

```Python
# test_source.py
def test_foo():
    """
    arrange: given foo that returns bar
    act: when foo is called
    assert: then bar is returned
    """
    result = foo()
    assert result == "bar"
```

### Fix TDO002

This linting rule is triggered by a test function in a test file with a
docstring that doesn't follow the documentation pattern. For example:

```Python
# test_source.py
def test_foo():
    """Test foo."""
    result = foo()
    assert result == "bar"
```

This example can be fixed by:

```Python
# test_source.py
def test_foo():
    """
    arrange: given foo that returns bar
    act: when foo is called
    assert: then bar is returned
    """
    result = foo()
    assert result == "bar"
```

The message of the linting rule should give you the specific problem with the
documentation. In general, the pattern is:

* start on the second line with the same indentation is the start of the
  docstring
* the starting line should begin with `arrange:` (or whatever was set using
  `--test-docs-patter`) followed by at least some words describing the test
  setup
* long test setup descriptions can be broken over multiple lines by indenting
  the lines after the first by one level (e.g., 4 spaces by default)
* this is followed by similar sections starting with `act:` describing the test
  execution and `assert:` describing the checks
* the last line should be indented the same as the start of the docstring

Below are some valid examples. Starting with a vanilla example:

```Python
# test_source.py
def test_foo():
    """
    arrange: given foo that returns bar
    act: when foo is called
    assert: then bar is returned
    """
    result = foo()
    assert result == "bar"
```

Here is an example where the test function is in a nested scope:

```Python
# test_source.py
class TestSuite:

    def test_foo():
        """
        arrange: given foo that returns bar
        act: when foo is called
        assert: then bar is returned
        """
        result = foo()
        assert result == "bar"
```

Here is an example where each of the descriptions go over multiple lines:

```Python
# test_source.py
def test_foo():
    """
    arrange: given foo
        that returns bar
    act: when foo
        is called
    assert: then bar
        is returned
    """
    result = foo()
    assert result == "bar"
```
