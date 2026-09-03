import math
import re


def normalize_whitespace(value):
    """
    Normalize whitespace while preserving line structure.
    """

    if value is None:
        return ""

    lines = value.strip().splitlines()

    normalized_lines = []

    for line in lines:
        normalized_lines.append(
            " ".join(line.strip().split())
        )

    return "\n".join(normalized_lines).strip()


def compare_exact(actual, expected):
    """
    Exact output comparison.
    """

    if actual is None:
        actual = ""

    if expected is None:
        expected = ""

    return actual == expected


def compare_whitespace(actual, expected):
    """
    Compare output while ignoring extra spaces,
    tabs and surrounding whitespace.
    """

    return (
        normalize_whitespace(actual)
        ==
        normalize_whitespace(expected)
    )


def parse_numbers(value):
    """
    Extract numeric values from output.

    Supports integers, decimals and scientific notation.
    """

    if value is None:
        return []

    pattern = r"""
        [-+]?
        (?:
            (?:\d+\.\d*)
            |
            (?:\.\d+)
            |
            (?:\d+)
        )
        (?:[eE][-+]?\d+)?
    """

    matches = re.findall(
        pattern,
        value,
        re.VERBOSE
    )

    return [float(number) for number in matches]


def compare_numeric(actual, expected):
    """
    Numeric comparison.

    Example:

        30
        30.0

    are considered equal.
    """

    actual_numbers = parse_numbers(actual)
    expected_numbers = parse_numbers(expected)

    if len(actual_numbers) != len(expected_numbers):
        return False

    for actual_value, expected_value in zip(
        actual_numbers,
        expected_numbers
    ):

        if not math.isclose(
            actual_value,
            expected_value,
            rel_tol=0,
            abs_tol=0
        ):
            return False

    return True


def compare_float(actual, expected, tolerance=0.000001):
    """
    Floating-point comparison using tolerance.
    """

    actual_numbers = parse_numbers(actual)
    expected_numbers = parse_numbers(expected)

    if len(actual_numbers) != len(expected_numbers):
        return False

    for actual_value, expected_value in zip(
        actual_numbers,
        expected_numbers
    ):

        if not math.isclose(
            actual_value,
            expected_value,
            rel_tol=0,
            abs_tol=tolerance
        ):
            return False

    return True


def compare_unordered(actual, expected):
    """
    Compare whitespace-separated output
    without considering order.
    """

    if actual is None:
        actual = ""

    if expected is None:
        expected = ""

    actual_tokens = normalize_whitespace(
        actual
    ).split()

    expected_tokens = normalize_whitespace(
        expected
    ).split()

    return sorted(actual_tokens) == sorted(
        expected_tokens
    )


def compare_output(
    actual,
    expected,
    comparison_type="WHITESPACE",
    tolerance=0.000001,
):
    """
    Main output comparison function.

    Supported comparison types:

        EXACT
        WHITESPACE
        NUMERIC
        FLOAT
        UNORDERED
    """

    if comparison_type == "EXACT":

        return compare_exact(
            actual,
            expected
        )

    if comparison_type == "WHITESPACE":

        return compare_whitespace(
            actual,
            expected
        )

    if comparison_type == "NUMERIC":

        return compare_numeric(
            actual,
            expected
        )

    if comparison_type == "FLOAT":

        return compare_float(
            actual,
            expected,
            tolerance
        )

    if comparison_type == "UNORDERED":

        return compare_unordered(
            actual,
            expected
        )

    # Safety fallback
    return compare_whitespace(
        actual,
        expected
    )