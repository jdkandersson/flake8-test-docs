"""A linter that checks test docstrings for the arrange/act/assert or given/when/then structure."""

import re
import argparse
import ast
from pathlib import Path
import sys
from typing import Iterable, NamedTuple

if sys.version_info < (3, 11):  # pragma: nocover
    import toml as tomllib
else:
    import tomllib

from flake8.options.manager import OptionManager

from astpretty import pprint


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
    f"Docstring not defined on test function, {MORE_INFO_BASE}#fix-{MISSING_CODE.lower()}"
)
INVALID_CODE = f"{ERROR_CODE_PREFIX}002"
INVALID_MSG_POSTFIX = f", {MORE_INFO_BASE}#fix-{INVALID_CODE.lower()}"
TEST_DOCS_PATTERN_ARG_NAME = "--test-docs-pattern"
TEST_DOCS_PATTERN_DEFAULT = "arrange/act/assert"
TEST_DOCS_FILENAME_PATTERN_ARG_NAME = "--test-docs-filename-pattern"
TEST_DOCS_FILENAME_PATTERN_DEFAULT = r"test_.*.py"
TEST_DOCS_FUNCTION_PATTERN_ARG_NAME = "--test-docs-function-pattern"
TEST_DOCS_FUNCTION_PATTERN_DEFAULT = r"test_.*"


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
        return f"the docstring should not be empty{INVALID_MSG_POSTFIX}"

    if not docstring.startswith("\n"):
        return f"the docstring should start with an empty line{INVALID_MSG_POSTFIX}"

    docstring_lines = docstring.splitlines()

    arrange_index = 1
    if not docstring_lines[arrange_index]:
        return (
            "there should only be a single new line at the start of the "
            f"docstring{INVALID_MSG_POSTFIX}"
        )
    if docs_pattern.arrange not in docstring_lines[arrange_index]:
        return (
            'the docstring should include "arrange" describing the test setup in line '
            f"{arrange_index} of the docstring{INVALID_MSG_POSTFIX}"
        )
    if not docstring_lines[arrange_index].startswith(" " * col_offset):
        return (
            f"the indentation of line {arrange_index} of the docstring should match the "
            f"indentation of the docstring{INVALID_MSG_POSTFIX}"
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
    def add_options(option_manager: OptionManager) -> None:  # pragma: nocover
        """Add additional options to flake8.

        Args:
            option_manager: The flake8 OptionManager.
        """
        option_manager.add_option(
            TEST_DOCS_PATTERN_ARG_NAME,
            default=TEST_DOCS_PATTERN_DEFAULT,
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
        assert test_docs_pattern_arg.count("/") == 2
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
        if not re.match(self._test_docs_filename_pattern, self._filename):
            return

        visitor = Visitor(self._test_docs_pattern, self._test_docs_function_pattern)
        visitor.visit(self._tree)
        yield from (
            (problem.lineno, problem.col_offset, problem.msg, type(self))
            for problem in visitor.problems
        )
