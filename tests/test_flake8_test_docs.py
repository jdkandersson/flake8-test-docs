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
            """
class TestSuite:
    def test_():
        pass
""",
            (f"3:4 {MISSING_MSG}",),
            id="missing docstring deeper nesting",
        ),
        pytest.param(
            '''
def test_():
    """"""
''',
            (f"3:4 the docstring should not be empty{INVALID_MSG_POSTFIX}",),
            id="invalid docstring empty",
        ),
        pytest.param(
            '''
class TestSuite:
    def test_():
        """"""
''',
            (f"4:8 the docstring should not be empty{INVALID_MSG_POSTFIX}",),
            id="invalid docstring empty deeper nesting",
        ),
        pytest.param(
            '''
def test_():
    """arrange"""
''',
            (f"3:4 the docstring should start with an empty line{INVALID_MSG_POSTFIX}",),
            id="invalid docstring not empty start line",
        ),
        pytest.param(
            '''
def test_():
    """
    """
''',
            (
                '3:4 the docstring should include "arrange" describing the test setup'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange missing",
        ),
        pytest.param(
            '''
def test_():
    """
arrange"""
''',
            (
                "3:4 the indentation of line 1 of the docstring should match the indentation of "
                "the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong column offset",
        ),
        pytest.param(
            '''
def test_():
    """

arrange"""
''',
            (
                "3:4 there should only be a single new line at the start of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange extra new line",
        ),
        pytest.param(
            '''
def test_():
    """
    given"""
''',
            (
                '3:4 line 1 of the docstring should start with "arrange" ',
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong word",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange"""
''',
            (
                '3:4 "arrange" should be followed by a colon (":") on line 1 of the docstring'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange missing colon",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange:"""
''',
            (
                '3:4 "arrange:" should be followed by a description of the test setup on line 1 '
                "of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange no description",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1

line 3"""
''',
            (
                "3:4 there should not be an empty line in the test setup description"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong newline in description",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
line 2"""
''',
            (
                "3:4 test setup description on line 2 should be indented by 4 more spaces than "
                '"arrange:" on line 1'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong multiline at start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    line 2"""
''',
            (
                "3:4 test setup description on line 2 should be indented by 4 more spaces than "
                '"arrange:" on line 1'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong multiline at docstring column offset",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
        line 2
line 3"""
''',
            (
                "3:4 test setup description on line 3 should be indented by 4 more spaces than "
                '"arrange:" on line 1'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong many lines at start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
        line 2
    line 3"""
''',
            (
                "3:4 test setup description on line 3 should be indented by 4 more spaces than "
                '"arrange:" on line 1'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong many lines at docstring column offset",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    """
''',
            (
                '3:4 the docstring should include "act" describing the test execution'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act missing",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1

act"""
''',
            (
                "3:4 there should not be a new line between the end of the test setup description "
                'and "act"'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act empty line before",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
act"""
''',
            (
                "3:4 the indentation of line 2 of the docstring should match the indentation of "
                "the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong column offset",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
        line 2
act"""
''',
            (
                "3:4 the indentation of line 3 of the docstring should match the indentation of "
                "the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong column offset arrange multi line",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    when"""
''',
            ('3:4 line 2 of the docstring should start with "act", ' f"{INVALID_MSG_POSTFIX}",),
            id="invalid docstring act wrong word",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act"""
''',
            (
                '3:4 "act" should be followed by a colon (":") on line 2 of the docstring'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act missing colon",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act:"""
''',
            (
                '3:4 "act:" should be followed by a description of the test execution on line 2 '
                "of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act no description",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2

line 4"""
''',
            (
                "3:4 there should not be an empty line in the test execution description"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong newline in description",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
line 3"""
''',
            (
                "3:4 test execution description on line 3 should be indented by 4 more spaces than "
                '"act:" on line 2'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong multiline at start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    line 3"""
''',
            (
                "3:4 test execution description on line 3 should be indented by 4 more spaces than "
                '"act:" on line 2'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong multiline at docstring column offset",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
        line 3
line 4"""
''',
            (
                "3:4 test execution description on line 4 should be indented by 4 more spaces than "
                '"act:" on line 2'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong many lines at start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
        line 3
    line 4"""
''',
            (
                "3:4 test setup description on line 4 should be indented by 4 more spaces than "
                '"act:" on line 2'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong many lines at docstring column offset",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    """
''',
            (
                '3:4 the docstring should include "assert" describing the test checks'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert missing",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2

assert"""
''',
            (
                "3:4 there should not be a new line between the end of the test execution "
                'description and "assert"'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert empty line before",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
assert"""
''',
            (
                "3:4 the indentation of line 3 of the docstring should match the indentation of "
                "the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong column offset",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
        line 3
assert"""
''',
            (
                "3:4 the indentation of line 4 of the docstring should match the indentation of "
                "the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong column offset act multi line",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    then"""
''',
            (
                f'3:4 line 3 of the docstring should start with "assert", '
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong word",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert"""
''',
            (
                '3:4 "assert" should be followed by a colon (":") on line 3 of the docstring'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert missing colon",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert:"""
''',
            (
                '3:4 "assert:" should be followed by a description of the test checks on line 3 '
                "of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert no description",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3

line 5"""
''',
            (
                "3:4 there should not be an empty line in the test check description"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong newline in description",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
line 4"""
''',
            (
                "3:4 test check description on line 4 should be indented by 4 more spaces than "
                '"assert:" on line 3'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong multiline at start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
    line 4"""
''',
            (
                "3:4 test check description on line 4 should be indented by 4 more spaces than "
                '"assert:" on line 3'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong multiline at docstring column offset",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
        line 4
line 5"""
''',
            (
                "3:4 test execution description on line 5 should be indented by 4 more spaces than "
                '"assert:" on line 3'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong many lines at start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
        line 4
    line 5"""
''',
            (
                "3:4 test setup description on line 5 should be indented by 4 more spaces than "
                '"assert:" on line 3'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong many lines at docstring column offset",
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
            (
                "3:4 there should not be an empty new line at the end of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring empty newline at end",
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
            (
                "3:4 the last line of the docstring should be indented in the same way as the "
                "start"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring ending wrong indent left",
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
            (
                "3:4 the last line of the docstring should be indented in the same way as the "
                "start"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring ending wrong indent right",
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
            (),
            id="valid docstring",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
        line 2
    act: line 3
    assert: line 4
    """
''',
            (),
            id="valid docstring multi line arrange",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
        line 2
        line 3
    act: line 4
    assert: line 5
    """
''',
            (),
            id="valid docstring many line arrange",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
        line 3
    assert: line 4
    """
''',
            (),
            id="valid docstring multi line act",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
        line 3
        line 4
    assert: line 5
    """
''',
            (),
            id="valid docstring many line act",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
        line 4
    """
''',
            (),
            id="valid docstring multi line assert",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act: line 2
    assert: line 3
        line 4
        line 5
    """
''',
            (),
            id="valid docstring many line assert",
        ),
        pytest.param(
            '''
class TestSuite:
    def test_():
        """
        arrange: line 1
        act: line 2
        assert: line 3
        """
''',
            (),
            id="valid docstring deeper indentation",
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
