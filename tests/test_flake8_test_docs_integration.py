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
    INVALID_MSG_POSTFIX,
    INVALID_CODE,
)


def test_help():
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
    (code_file := base_path / "test_.py").write_text(f'"""Docstring."""\n\n\n{code}')
    return code_file


def test_fail(tmp_path: Path):
    """
    given: file with Python code that fails the linting
    when: the flake8 is run against the code
    then: the process exits with non-zero code and includes the error message
    """
    code_file = create_code_file('def test_():\n    """Docstring."""\n', tmp_path)

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
