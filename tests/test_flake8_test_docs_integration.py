"""Tests for plugin."""

import subprocess
import sys
from pathlib import Path

import pytest

from flake8_test_docs import (
    TEST_DOCS_PATTERN_ARG_NAME,
    TEST_DOCS_FILENAME_PATTERN_ARG_NAME,
    TEST_DOCS_FUNCTION_PATTERN_ARG_NAME,
    INVALID_MSG_POSTFIX,
    MISSING_CODE,
    INVALID_CODE,
)


def test_help():
    """
    given: linter
    when: the flake8 help message is generated
    then: plugin is registered with flake8
    """
    with subprocess.Popen(
        f"{sys.executable} -m flake8 --help",
        stdout=subprocess.PIPE,
        shell=True,
    ) as proc:
        stdout = proc.communicate()[0].decode(encoding="utf-8")

        assert "flake8-test-docs" in stdout
        assert TEST_DOCS_PATTERN_ARG_NAME in stdout
        assert TEST_DOCS_FILENAME_PATTERN_ARG_NAME in stdout
        assert TEST_DOCS_FUNCTION_PATTERN_ARG_NAME in stdout


def create_code_file(code: str, filename: str, base_path: Path) -> Path:
    """Create the code file with the given code.

    Args:
        code: The code to write to the file.
        base_path: The path to create the file within

    Returns:
        The path to the code file.
    """
    (code_file := base_path / filename).write_text(f'"""Docstring."""\n\n{code}')
    return code_file


def test_fail(tmp_path: Path):
    """
    given: file with Python code that fails the linting
    when: the flake8 is run against the code
    then: the process exits with non-zero code and includes the error message
    """
    code_file = create_code_file('\ndef test_():\n    """Docstring."""\n', "test_.py", tmp_path)

    with subprocess.Popen(
        f"{sys.executable} -m flake8 {code_file}",
        stdout=subprocess.PIPE,
        shell=True,
    ) as proc:
        stdout = proc.communicate()[0].decode(encoding="utf-8")

        assert (
            f"{INVALID_CODE} the docstring should start with an empty line{INVALID_MSG_POSTFIX}"
            in stdout
        )
        assert proc.returncode


@pytest.mark.parametrize(
    "docs_pattern",
    [
        pytest.param("", id="empty"),
        pytest.param("given", id="only 1"),
        pytest.param("given/when", id="only 2"),
        pytest.param("given/when/then/extra", id="4 provided"),
    ],
)
def test_invalid_docs_pattern(docs_pattern: str, tmp_path: Path):
    """
    given: invalid value for the docs pattern argument
    when: the flake8 is run against the code
    then: the process exits with non-zero code
    """
    code = '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
    """
'''
    code_file = create_code_file(code, "test_.py", tmp_path)

    with subprocess.Popen(
        f"{sys.executable} -m flake8 {code_file} {TEST_DOCS_PATTERN_ARG_NAME} {docs_pattern}",
        stdout=subprocess.PIPE,
        shell=True,
    ) as proc:
        proc.communicate()

        assert proc.returncode


@pytest.mark.parametrize(
    "code, filename, extra_args",
    [
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
    """
''',
            "test_.py",
            "",
            id="default",
        ),
        pytest.param(
            '''
def test_():
    """
    given: line 1
    when: line 2
    then: line 3
    """
''',
            "test_.py",
            f"{TEST_DOCS_PATTERN_ARG_NAME} given/when/then",
            id="custom docs pattern",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
    """
''',
            "_test.py",
            f"{TEST_DOCS_FILENAME_PATTERN_ARG_NAME} .*_test.py",
            id="custom filename pattern",
        ),
        pytest.param(
            '''
def _test():
    """
    arrange: line 1
    act: line 2
    assert: line 3
    """
''',
            "test_.py",
            f"{TEST_DOCS_FUNCTION_PATTERN_ARG_NAME} .*_test",
            id="custom function pattern",
        ),
        pytest.param(
            f"""
def test_():  # noqa: {MISSING_CODE}
    pass
""",
            "test_.py",
            "",
            id=f"{MISSING_CODE} disabled",
        ),
        pytest.param(
            f'''
def test_():
    """"""  # noqa: {INVALID_CODE}
''',
            "test_.py",
            "",
            id=f"{INVALID_CODE} disabled",
        ),
        pytest.param(
            '''
def test_():
  """
  arrange: line 1
    line 2
  act: line 3
    line 4
  assert: line 5
    line 6
  """
''',
            "test_.py",
            "--indent-size 2",
            id="changed indentation",
        ),
    ],
)
def test_integration_pass(code: str, filename: str, extra_args: str, tmp_path: Path):
    """
    given: file with Python code that passes the linting
    when: the flake8 is run against the code
    then: the process exits with zero code and empty stdout
    """
    code_file = create_code_file(code, filename, tmp_path)

    with subprocess.Popen(
        f"{sys.executable} -m flake8 {code_file} {extra_args} --ignore D205,D400,D103",
        stdout=subprocess.PIPE,
        shell=True,
    ) as proc:
        stdout = proc.communicate()[0].decode(encoding="utf-8")

        assert not stdout, stdout
        assert not proc.returncode
