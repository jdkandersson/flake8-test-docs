"""A linter that checks test docstrings for the arrange/act/assert or given/when/then structure."""

from functools import wraps
import re
import argparse
import ast
from pathlib import Path
import sys
from typing import Iterable, NamedTuple, Callable

if sys.version_info < (3, 11):  # pragma: nocover
    import toml as tomllib
else:
    import tomllib

from flake8.options.manager import OptionManager


ERROR_CODE_PREFIX = next(
    iter(
        tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["tool"]["poetry"][
            "plugins"
        ]["flake8.extension"].keys()
    )
)
MORE_INFO_BASE = "more information: https://github.com/jdkandersson/flake8-test-docs"
MISSING_CODE = f"{ERROR_CODE_PREFIX}001"
MISSING_MSG = (
    f"{MISSING_CODE} Docstring not defined on test function, "
    f"{MORE_INFO_BASE}#fix-{MISSING_CODE.lower()}"
)
INVALID_CODE = f"{ERROR_CODE_PREFIX}002"
INVALID_MSG_POSTFIX = f", {MORE_INFO_BASE}#fix-{INVALID_CODE.lower()}"
TEST_DOCS_PATTERN_ARG_NAME = "--test-docs-pattern"
TEST_DOCS_PATTERN_DEFAULT = "arrange/act/assert"
TEST_DOCS_FILENAME_PATTERN_ARG_NAME = "--test-docs-filename-pattern"
TEST_DOCS_FILENAME_PATTERN_DEFAULT = r"test_.*.py"
TEST_DOCS_FUNCTION_PATTERN_ARG_NAME = "--test-docs-function-pattern"
TEST_DOCS_FUNCTION_PATTERN_DEFAULT = r"test_.*"
ARRANGE_DESCRIPTION = "setup"
ACT_DESCRIPTION = "execution"
ASSERT_DESCRIPTION = "checks"


# Helper function for option management, tested in integration tests
def _cli_arg_name_to_attr(cli_arg_name: str) -> str:
    """Transform CLI argument name to the attribute name on the namespace.

    Args:
        cli_arg_name: The CLI argument name to transform.

    Returns:
        The namespace name for the argument.
    """
    return cli_arg_name.lstrip("-").replace("-", "_")  # pragma: nocover


class DocsPattern(NamedTuple):
    """Represents the pattern for the docstring.

    Attrs:
        arrange: The prefix for the test setup description.
        act: The prefix for the test execution description.
        assert_: The prefix for the test check description.
    """

    arrange: str
    act: str
    assert_: str


class Section(NamedTuple):
    """Information about a section.

    Attrs:
        index: The index of the first line of the section in the docstring.
        name: A short description of the section.
        description: What the section does.
        next_section_name: The name of the next section or None if it is the last section.
    """

    index: int
    name: str
    description: str
    next_section_name: str | None


def _append_invalid_msg_prefix_postfix(
    func: Callable[..., str | None]
) -> Callable[..., str | None]:
    """Add the invalid message postfix to the return value.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrap the function."""
        if (return_value := func(*args, **kwargs)) is None:
            return None
        return f"{INVALID_CODE} {return_value}{INVALID_MSG_POSTFIX}"

    return wrapper


def _section_start_problem_message(
    line: str, section: Section, col_offset: int, expected_section_prefix: str
) -> str | None:
    """Check the first line of a section.

    Args:
        line: The line to check
        section: Information about the section.
        col_offset: The column offset where the docstring definition starts.
        expected_section_prefix: The prefix expected at the start of a section.

    Returns:
        The problem description if the line has problems or None.
    """
    if not line:
        return (
            "there should only be a single empty line at the start of the docstring, found an "
            f"empty line on line {section.index}"
        )
    if section.name not in line:
        return (
            f'the docstring should include "{section.name}" describing the test '
            f"{section.description} on line {section.index} of the docstring"
        )
    if not line.startswith(expected_section_prefix):
        return (
            f"the indentation of line {section.index} of the docstring should match the "
            "indentation of the docstring"
        )
    if not line[col_offset:].startswith(f"{section.name}:"):
        return f'line {section.index} of the docstring should start with "{section.name}:"'
    if not line[col_offset + len(section.name) + 1 :]:
        return (
            f'"{section.name}:" should be followed by a description of the test '
            f"{section.description} on "
            f"line {section.index} of the docstring"
        )

    return None


def _next_section_start(
    line: str, next_section_name: str | None, expected_section_prefix: str
) -> bool:
    """Detect whether the line is the start of the next section.

    The next section is defined to be either that the line starts with the next section name after
    any whitespace or that the line starts with exactly the number of whitespace characters
    expected for a new section.

    Args:
        line: The line to check.
        next_section_name: The name of the next section or None if it is the last section.
        expected_section_prefix: The prefix expected at the start of a section.

    Returns:
        Whether the line is the start of the next section.
    """
    if next_section_name is not None and line.strip().startswith(next_section_name):
        return True

    if len(line) < len(expected_section_prefix) and line.count(" ") == len(line):
        return True

    if line.startswith(expected_section_prefix) and not line[
        len(expected_section_prefix) :
    ].startswith(" "):
        return True

    return False


def _remaining_description_problem_message(
    section: Section,
    docstring_lines: list[str],
    expected_section_prefix: str,
    expected_description_prefix: str,
    expected_indentation: int,
) -> tuple[str | None, int]:
    """Check the remaining description of a section after the first line.

    Args:
        section: Information about the section.
        docstring_lines: All the lines of the docstring.
        expected_section_prefix: The prefix expected at the start of a section.
        expected_description_prefix: The prefix expected at the start of description line.
        expected_indentation: The number of indentation characters.

    Returns:
        The problem message if there is a problem or None and the index of the start index of the
        next section.
    """
    line_index = section.index + 1
    for line_index in range(line_index, len(docstring_lines)):
        line = docstring_lines[line_index]

        if not line:
            return (
                f"there should not be an empty line in the test {section.description} description "
                f"on line {line_index} of the docstring"
            ), line_index

        # Detecting the start of the next section
        if _next_section_start(
            line=line,
            next_section_name=section.next_section_name,
            expected_section_prefix=expected_section_prefix,
        ):
            break

        if not line.startswith(expected_description_prefix) or line[
            len(expected_description_prefix) :
        ].startswith(" "):
            return (
                f"test {section.description} description on line {line_index} should be indented "
                f'by {expected_indentation} more spaces than "{section.name}:" on line '
                f"{section.index}"
            ), line_index

    return None, line_index


@_append_invalid_msg_prefix_postfix
def _docstring_problem_message(
    docstring: str, col_offset: int, docs_pattern: DocsPattern
) -> str | None:
    """Get the problem message for a docstring.

    Args:
        docstring: The docstring to check.
        col_offset: The column offset where the docstring definition starts.
        docs_pattern: The pattern the docstring should follow.

    Returns:
        The problem message explaining what is wrong with the docstring or None if it is valid.
    """
    if not docstring:
        return "the docstring should not be empty"

    if not docstring.startswith("\n"):
        return "the docstring should start with an empty line"

    docstring_lines = docstring.splitlines()
    expected_section_prefix = " " * col_offset
    expected_indentation = 4
    expected_description_prefix = f"{expected_section_prefix}{' ' * expected_indentation}"

    sections = zip(
        docs_pattern,
        (ARRANGE_DESCRIPTION, ACT_DESCRIPTION, ASSERT_DESCRIPTION),
        (*docs_pattern[1:], None),
    )
    section_index = 1
    for section_name, section_description, next_section_name in sections:
        section = Section(
            index=section_index,
            name=section_name,
            description=section_description,
            next_section_name=next_section_name,
        )
        start_problem = _section_start_problem_message(
            line=docstring_lines[section.index],
            section=section,
            col_offset=col_offset,
            expected_section_prefix=expected_section_prefix,
        )
        if start_problem is not None:
            return start_problem
        description_problem, section_index = _remaining_description_problem_message(
            section=section,
            docstring_lines=docstring_lines,
            expected_section_prefix=expected_section_prefix,
            expected_description_prefix=expected_description_prefix,
            expected_indentation=expected_indentation,
        )
        if description_problem is not None:
            return description_problem

    if (
        len(docstring_lines) <= section_index
        or docstring_lines[section_index] != expected_section_prefix
    ):
        return (
            f"the indentation of the last line of the docstring at line {section_index} should "
            "match the indentation of the docstring"
        )

    return None


class Problem(NamedTuple):
    """Represents a problem within the code.

    Attrs:
        lineno: The line number the problem occurred on
        col_offset: The column the problem occurred on
        msg: The message explaining the problem
    """

    lineno: int
    col_offset: int
    msg: str


class Visitor(ast.NodeVisitor):
    """Visits AST nodes and check docstrings of test functions.

    Attrs:
        problems: All the problems that were encountered.
    """

    problems: list[Problem]
    _test_docs_pattern: DocsPattern
    _test_function_pattern: str

    def __init__(self, test_docs_pattern: DocsPattern, test_function_pattern: str) -> None:
        """Construct."""
        self.problems = []
        self._test_docs_pattern = test_docs_pattern
        self._test_function_pattern = test_function_pattern

    # The function must be called the same as the name of the node
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pylint: disable=invalid-name
        """Visit all FunctionDef nodes.

        Args:
            node: The FunctionDef node.
        """
        if re.match(self._test_function_pattern, node.name):
            if (
                not node.body
                or not isinstance(node.body, list)
                or not isinstance(node.body[0], ast.Expr)
                or not hasattr(node.body[0], "value")
                or not isinstance(node.body[0].value, ast.Constant)
                or not isinstance(node.body[0].value.value, str)
            ):
                self.problems.append(Problem(node.lineno, node.col_offset, MISSING_MSG))
            else:
                if problem_message := _docstring_problem_message(
                    node.body[0].value.value,
                    node.body[0].value.col_offset,
                    self._test_docs_pattern,
                ):
                    self.problems.append(
                        Problem(
                            node.body[0].value.lineno,
                            node.body[0].value.col_offset,
                            problem_message,
                        )
                    )

        # Ensure recursion continues
        self.generic_visit(node)


class Plugin:
    """Checks test docstrings for the arrange/act/assert or given/when/then structure.

    Attrs:
        name: The name of the plugin.
        version: The version of the plugin.
    """

    name = __name__
    version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["tool"]["poetry"][
        "version"
    ]
    _test_docs_pattern: DocsPattern = DocsPattern(*TEST_DOCS_PATTERN_DEFAULT.split("/"))
    _test_docs_filename_pattern: str = TEST_DOCS_FILENAME_PATTERN_DEFAULT
    _test_docs_function_pattern: str = TEST_DOCS_FUNCTION_PATTERN_DEFAULT
    _filename: str

    def __init__(self, tree: ast.AST, filename: str) -> None:
        """Construct.

        Args:
            tree: The AST syntax tree for a file.
            filename: The name of the file being processed.
        """
        self._tree = tree
        self._filename = filename

    # No coverage since this only occurs from the command line
    @staticmethod
    def _check_docs_pattern(value: str) -> str:  # pragma: nocover
        """Check the docs pattern argument.

        Args:
            value: The docs pattern argument value to check.

        Returns:
            The value if it is valid.

        Raises:
            ValueError: if the value is invalid.
        """
        if value.count("/") != 2:
            raise ValueError(
                f"the {TEST_DOCS_PATTERN_ARG_NAME} must follow the pattern <given>/<when>/<when>, "
                f"got: {value}"
            )
        return value

    # No coverage since this only occurs from the command line
    @staticmethod
    def add_options(option_manager: OptionManager) -> None:  # pragma: nocover
        """Add additional options to flake8.

        Args:
            option_manager: The flake8 OptionManager.
        """
        option_manager.add_option(
            TEST_DOCS_PATTERN_ARG_NAME,
            default=TEST_DOCS_PATTERN_DEFAULT,
            type=Plugin._check_docs_pattern,
            parse_from_config=True,
            help=(
                "The expected test docs pattern, needs to be of the form <word>/<word>/<word> "
                "which represents an equivalent of the arrange/act/assert, e.g., given/when/then. "
                f"(Default: {TEST_DOCS_PATTERN_DEFAULT})"
            ),
        )
        option_manager.add_option(
            TEST_DOCS_FILENAME_PATTERN_ARG_NAME,
            default=TEST_DOCS_FILENAME_PATTERN_DEFAULT,
            parse_from_config=True,
            help=(
                "The pattern to match test files with. "
                f"(Default: {TEST_DOCS_FILENAME_PATTERN_DEFAULT})"
            ),
        )
        option_manager.add_option(
            TEST_DOCS_FUNCTION_PATTERN_ARG_NAME,
            default=TEST_DOCS_FUNCTION_PATTERN_DEFAULT,
            parse_from_config=True,
            help=(
                "The pattern to match test functions with. "
                f"(Default: {TEST_DOCS_FUNCTION_PATTERN_DEFAULT})"
            ),
        )

    # No coverage since this only occurs from the command line
    @classmethod
    def parse_options(cls, options: argparse.Namespace) -> None:  # pragma: nocover
        """Record the value of the options.

        Args:
            options: The options passed to flake8.
        """
        test_docs_pattern_arg = (
            getattr(options, _cli_arg_name_to_attr(TEST_DOCS_PATTERN_ARG_NAME), None)
            or TEST_DOCS_PATTERN_DEFAULT
        )
        cls._test_docs_pattern = DocsPattern(*test_docs_pattern_arg.split("/"))
        cls._test_docs_filename_pattern = (
            getattr(options, _cli_arg_name_to_attr(TEST_DOCS_FILENAME_PATTERN_ARG_NAME), None)
            or cls._test_docs_filename_pattern
        )
        cls._test_docs_function_pattern = (
            getattr(options, _cli_arg_name_to_attr(TEST_DOCS_FUNCTION_PATTERN_ARG_NAME), None)
            or cls._test_docs_function_pattern
        )

    def run(self) -> Iterable[tuple[int, int, str, type["Plugin"]]]:
        """Lint a file.

        Yields:
            All the issues that were found.
        """
        if not re.match(self._test_docs_filename_pattern, Path(self._filename).name):
            return

        visitor = Visitor(self._test_docs_pattern, self._test_docs_function_pattern)
        visitor.visit(self._tree)
        yield from (
            (problem.lineno, problem.col_offset, problem.msg, type(self))
            for problem in visitor.problems
        )
