"""Unit tests for plugin."""

from __future__ import annotations

import ast

import hypothesis
import pytest
from hypothesis import strategies

from flake8_test_docs import (
    ACT_DESCRIPTION,
    ARRANGE_DESCRIPTION,
    ASSERT_DESCRIPTION,
    INVALID_CODE,
    INVALID_MSG_POSTFIX,
    MISSING_MSG,
    Plugin,
)


def _result(code: str, filename: str = "test_.py") -> tuple[str, ...]:
    """Generate linting results.

    Args:
        code: The code to check.
        filename: The name of the file being checked.

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
            (f"3:4 {INVALID_CODE} the docstring should not be empty{INVALID_MSG_POSTFIX}",),
            id="invalid docstring empty",
        ),
        pytest.param(
            '''
class TestSuite:
    def test_():
        """"""
''',
            (f"4:8 {INVALID_CODE} the docstring should not be empty{INVALID_MSG_POSTFIX}",),
            id="invalid docstring empty deeper nesting",
        ),
        pytest.param(
            '''
def test_():
    """arrange"""
''',
            (
                f"3:4 {INVALID_CODE} the docstring should start with an empty line"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring not empty start line",
        ),
        pytest.param(
            '''
def test_():
    """
    """
''',
            (
                f'3:4 {INVALID_CODE} the docstring should include "arrange" describing the test '
                f"{ARRANGE_DESCRIPTION} on line 1 of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of line 1 of the docstring should match the "
                "indentation of the docstring"
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
                f"3:4 {INVALID_CODE} there should only be a single empty line at the start of "
                "the docstring, found an empty line on line 1"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange extra new line",
        ),
        pytest.param(
            '''
def test_():
    """


arrange"""
''',
            (
                f"3:4 {INVALID_CODE} there should only be a single empty line at the start of the "
                "docstring, found an empty line on line 1"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange many extra new line",
        ),
        pytest.param(
            '''
def test_():
    """
    given arrange"""
''',
            (
                f'3:4 {INVALID_CODE} line 1 of the docstring should start with "arrange:"'
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
                f'3:4 {INVALID_CODE} line 1 of the docstring should start with "arrange:"'
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
                f'3:4 {INVALID_CODE} "arrange:" should be followed by a description of the test '
                f"{ARRANGE_DESCRIPTION} on line 1 of the docstring"
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
                f"3:4 {INVALID_CODE} there should not be an empty line in the test "
                f"{ARRANGE_DESCRIPTION} description on line 2 of the docstring"
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
                f"3:4 {INVALID_CODE} test {ARRANGE_DESCRIPTION} description on line 2 should be "
                'indented by 4 more spaces than "arrange:" on line 1'
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
                f"3:4 {INVALID_CODE} test {ARRANGE_DESCRIPTION} description on line 2 should be "
                'indented by 4 more spaces than "arrange:" on line 1'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong multiline past column offset + 4",
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
                f"3:4 {INVALID_CODE} test {ARRANGE_DESCRIPTION} description on line 3 should be "
                'indented by 4 more spaces than "arrange:" on line 1'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring arrange wrong many lines at start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    """
''',
            (
                f'3:4 {INVALID_CODE} the docstring should include "act" describing the test '
                f"{ACT_DESCRIPTION} on line 2 of the docstring"
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
                f"3:4 {INVALID_CODE} there should not be an empty line in the test "
                f"{ARRANGE_DESCRIPTION} description on line 2 of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of line 2 of the docstring should match the "
                "indentation of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of line 3 of the docstring should match the "
                "indentation of the docstring"
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
            (
                f'3:4 {INVALID_CODE} the docstring should include "act" describing the test '
                f"{ACT_DESCRIPTION} on line 2 of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong word",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    when act"""
''',
            (
                f'3:4 {INVALID_CODE} line 2 of the docstring should start with "act:"'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring act wrong start",
        ),
        pytest.param(
            '''
def test_():
    """
    arrange: line 1
    act"""
''',
            (
                f'3:4 {INVALID_CODE} line 2 of the docstring should start with "act:"'
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
                f'3:4 {INVALID_CODE} "act:" should be followed by a description of the test '
                f"{ACT_DESCRIPTION} on line 2 of the docstring"
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
                f"3:4 {INVALID_CODE} there should not be an empty line in the test "
                f"{ACT_DESCRIPTION} description on line 3 of the docstring"
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
                f"3:4 {INVALID_CODE} test {ACT_DESCRIPTION} description on line 3 should be "
                'indented by 4 more spaces than "act:" on line 2'
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
        line 3
line 4"""
''',
            (
                f"3:4 {INVALID_CODE} test {ACT_DESCRIPTION} description on line 4 should be "
                'indented by 4 more spaces than "act:" on line 2'
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
    """
''',
            (
                f'3:4 {INVALID_CODE} the docstring should include "assert" describing the test '
                f"{ASSERT_DESCRIPTION} on line 3 of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of line 3 of the docstring should match the "
                "indentation of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of line 3 of the docstring should match the "
                "indentation of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of line 4 of the docstring should match the "
                "indentation of the docstring"
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
                f'3:4 {INVALID_CODE} the docstring should include "assert" describing the test '
                f"{ASSERT_DESCRIPTION} on line 3 of the docstring"
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
    then assert"""
''',
            (
                f'3:4 {INVALID_CODE} line 3 of the docstring should start with "assert:"'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring assert wrong start",
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
                f'3:4 {INVALID_CODE} line 3 of the docstring should start with "assert:"'
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
                f'3:4 {INVALID_CODE} "assert:" should be followed by a description of the test '
                f"{ASSERT_DESCRIPTION} on line 3 of the docstring"
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
                f"3:4 {INVALID_CODE} there should not be an empty line in the test "
                f"{ASSERT_DESCRIPTION} description on line 4 of the docstring"
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
                f"3:4 {INVALID_CODE} test {ASSERT_DESCRIPTION} description on line 4 should be "
                'indented by 4 more spaces than "assert:" on line 3'
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
                f"3:4 {INVALID_CODE} the indentation of the last line of the docstring at line 4 "
                "should match the indentation of the docstring"
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
                f"3:4 {INVALID_CODE} test {ASSERT_DESCRIPTION} description on line 5 should be "
                'indented by 4 more spaces than "assert:" on line 3'
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
                f"3:4 {INVALID_CODE} the indentation of the last line of the docstring at line 5 "
                "should match the indentation of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of the last line of the docstring at line 4 "
                "should match the indentation of the docstring"
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
                f"3:4 {INVALID_CODE} the indentation of the last line of the docstring at line 4 "
                "should match the indentation of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring single space newline at end",
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
                f"3:4 {INVALID_CODE} the indentation of the last line of the docstring at line 4 "
                "should match the indentation of the docstring"
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring ending wrong indent just left",
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
                f"3:4 {INVALID_CODE} test {ASSERT_DESCRIPTION} description on line 4 should be "
                'indented by 4 more spaces than "assert:" on line 3'
                f"{INVALID_MSG_POSTFIX}",
            ),
            id="invalid docstring ending wrong indent just right",
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
                f"3:4 {INVALID_CODE} the indentation of the last line of the docstring at line 4 "
                "should match the indentation of the docstring"
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
def test_plugin_invalid(code: str, expected_result: tuple[str, ...]):
    """
    given: code
    when: linting is run on the code
    then: the expected result is returned
    """
    assert _result(code) == expected_result


@pytest.mark.parametrize(
    "filename, expected_result",
    [
        pytest.param("test_.py", (f"2:0 {MISSING_MSG}",), id="test file"),
        pytest.param("file.py", (), id="not test file"),
        pytest.param("test_dpy", (), id="not test file missing ."),
    ],
)
def test_plugin_filename(filename: str, expected_result: tuple[str, ...]):
    """
    given: code and filename
    when: linting is run on the code
    then: the expected result is returned
    """
    code = """
def test_():
    pass
"""

    assert _result(code, filename) == expected_result


_TEST_DOCS_SECTION_PREFIX_REGEX = r"    "
_TEST_DOCS_WORD_REGEX = r"(\w+ ?)+"
_TEST_DOCS_SECTION_START_REGEX = rf": {_TEST_DOCS_WORD_REGEX}\n"
_TEST_DOCS_OPTIONAL_LINE_REGEX = (
    rf"({_TEST_DOCS_SECTION_PREFIX_REGEX * 2}{_TEST_DOCS_WORD_REGEX}\n)*"
)
_TEST_DOCS_REGEX = (
    f"^\n"
    f"{_TEST_DOCS_SECTION_PREFIX_REGEX}arrange{_TEST_DOCS_SECTION_START_REGEX}"
    f"{_TEST_DOCS_OPTIONAL_LINE_REGEX}"
    f"{_TEST_DOCS_SECTION_PREFIX_REGEX}act{_TEST_DOCS_SECTION_START_REGEX}"
    f"{_TEST_DOCS_OPTIONAL_LINE_REGEX}"
    f"{_TEST_DOCS_SECTION_PREFIX_REGEX}assert{_TEST_DOCS_SECTION_START_REGEX}"
    f"{_TEST_DOCS_OPTIONAL_LINE_REGEX}"
    f"{_TEST_DOCS_SECTION_PREFIX_REGEX}$"
)


@hypothesis.settings(suppress_health_check=(hypothesis.HealthCheck.too_slow,))
@hypothesis.given(strategies.from_regex(_TEST_DOCS_REGEX))
def test_hypothesis(source: str):
    """
    given: generated docstring
    when: linting is run on the code
    then: empty results are returned
    """
    code = f'''
def test_():
    """{source}"""
'''

    assert not _result(code)
