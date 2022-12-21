"""Tests for plugin."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from flake8_test_docs import (
    Plugin,
    TEST_DOCS_PATTERN_ARG_NAME,
    TEST_DOCS_FILENAME_PATTERN_ARG_NAME,
    TEST_DOCS_FUNCTION_PATTERN_ARG_NAME,
    INVALID_MSG,
    MISSING_MSG,
)


def _result(code: str, filename: str = "test_.py") -> tuple[str, ...]:
    """Generate linting results.

    Args:
        code: The code to convert.

    Returns:
        The linting result.
    """
    tree = ast.parse(code)
    plugin = Plugin(tree, filename)
    return tuple(f"{line}:{col} {msg}" for line, col, msg, _ in plugin.run())


@pytest.mark.parametrize(
    "code, expected_result",
    [
        pytest.param("", (), id="trivial"),
        pytest.param(
            """
def test_():
    pass
""",
            (f"2:0 {MISSING_MSG}",),
            id="missing docstring",
        ),
        pytest.param(
            '''
def test_():
    """"""
''',
            (f"3:4 {INVALID_MSG}",),
            id="invalid docstring",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange:
    act:
    assert:
    """
''',
            (),
            id="valid docstring",
        ),
        pytest.param(
            """
def function_1():
    pass
""",
            (),
            id="missing docstring not test function",
        ),
        pytest.param(
            '''
def function_1():
    """"""
''',
            (),
            id="invalid docstring not test function",
        ),
    ],
)
def test_plugin(code: str, expected_result: tuple[str, ...]):
    """
    given: code
    when: linting is run on the code
    then: the expected result is returned
    """
    assert _result(code) == expected_result


def test_integration_help():
    """
    given:
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


def create_code_file(code: str, base_path: Path) -> Path:
    """Create the code file with the given code.

    Args:
        code: The code to write to the file.
        base_path: The path to create the file within

    Returns:
        The path to the code file.
    """
    (code_file := base_path / "code.py").write_text(f'"""Docstring."""\n\n{code}')
    return code_file
