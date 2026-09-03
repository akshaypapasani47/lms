from . import get_runner
from .comparator import compare_output

# def normalize_output(value):
#     """
#     Normalize program output before comparison.

#     - Removes leading/trailing whitespace.
#     - Removes extra spaces/tabs inside each line.
#     - Preserves line structure.
#     """

#     if value is None:
#         return ""

#     lines = str(value).strip().splitlines()

#     normalized_lines = []

#     for line in lines:
#         normalized_lines.append(
#             " ".join(line.strip().split())
#         )

#     return "\n".join(normalized_lines).strip()


def evaluate_programming_question(
    question,
    submitted_code
):
    """
    Evaluate a programming question against
    all configured test cases.
    """

    # ------------------------------------------------------
    # NO CODE
    # ------------------------------------------------------

    if not submitted_code or not submitted_code.strip():

        return {
            "marks": 0,
            "max_marks": question.marks,
            "passed": 0,
            "total_tests": 0,
            "feedback": "No code submitted.",
            "status": "NO_CODE",
            "test_results": [],
        }


    # ------------------------------------------------------
    # LANGUAGE CHECK
    # ------------------------------------------------------

    if not question.language:

        return {
            "marks": 0,
            "max_marks": question.marks,
            "passed": 0,
            "total_tests": 0,
            "feedback": (
                "Programming language is not configured."
            ),
            "status": "CONFIGURATION_ERROR",
            "test_results": [],
        }


    # ------------------------------------------------------
    # GET TEST CASES
    # ------------------------------------------------------

    test_cases = (
        question.test_cases
        .all()
        .order_by("order")
    )


    if not test_cases.exists():

        return {
            "marks": 0,
            "max_marks": question.marks,
            "passed": 0,
            "total_tests": 0,
            "feedback": (
                "No test cases configured."
            ),
            "status": "NO_TEST_CASES",
            "test_results": [],
        }


    # ------------------------------------------------------
    # GET RUNNER
    # ------------------------------------------------------

    try:

        runner = get_runner(
            question.language
        )

    except ValueError as error:

        return {
            "marks": 0,
            "max_marks": question.marks,
            "passed": 0,
            "total_tests": test_cases.count(),
            "feedback": str(error),
            "status": "CONFIGURATION_ERROR",
            "test_results": [],
        }


    # ------------------------------------------------------
    # EVALUATION VARIABLES
    # ------------------------------------------------------

    total_awarded_marks = 0
    passed_tests = 0

    test_results = []


    # ------------------------------------------------------
    # RUN EVERY TEST CASE
    # ------------------------------------------------------

    for test_case in test_cases:

        try:

            result = runner.run(
                code=submitted_code,
                input_data=test_case.input_data or "",
            )

        except Exception as error:

            test_results.append({

                "test_case_id":
                    test_case.id,

                "order":
                    test_case.order,

                "passed":
                    False,

                "status":
                    "ERROR",

                "marks":
                    0,

                "max_marks":
                    test_case.marks,

                "execution_time":
                    0,

                "feedback":
                    str(error),

                "actual_output":
                    "",

                "expected_output":
                    test_case.expected_output,

                "is_hidden":
                    test_case.is_hidden,

            })

            continue


        # --------------------------------------------------
        # DETERMINE STATUS
        # --------------------------------------------------

        if result.compile_error:

            passed = False

            status = "COMPILE_ERROR"

            feedback = (
                result.error
                or
                "Compilation failed."
            )


        elif result.timed_out:

            passed = False

            status = "TIMEOUT"

            feedback = (
                "Execution time exceeded."
            )


        elif not result.success:

            passed = False

            status = "RUNTIME_ERROR"

            feedback = (
                result.error
                or
                "Program execution failed."
            )


        else:

            # ----------------------------------------------
            # COMPARE OUTPUT
            # ----------------------------------------------

            passed = compare_output(

                actual=result.output,

                expected=test_case.expected_output,

                comparison_type=(
                    test_case.comparison_type
                ),

                tolerance=(
                    test_case.tolerance
                ),

            )


            if passed:

                status = "PASSED"

                feedback = (
                    "Test case passed."
                )

            else:

                status = "WRONG_ANSWER"

                feedback = (
                    "Output does not match "
                    "the expected output."
                )


        # --------------------------------------------------
        # MARKS
        # --------------------------------------------------

        if passed:

            test_marks = test_case.marks

            total_awarded_marks += (
                test_marks
            )

            passed_tests += 1

        else:

            test_marks = 0


        # --------------------------------------------------
        # STORE RESULT
        # --------------------------------------------------

        test_results.append({

            "test_case_id":
                test_case.id,

            "order":
                test_case.order,

            "passed":
                passed,

            "status":
                status,

            "marks":
                test_marks,

            "max_marks":
                test_case.marks,

            "execution_time":
                result.execution_time,

            "feedback":
                feedback,

            "actual_output":
                result.output,

            "expected_output":
                test_case.expected_output,

            "is_hidden":
                test_case.is_hidden,

        })


    # ------------------------------------------------------
    # LIMIT MARKS TO QUESTION MARKS
    # ------------------------------------------------------

    total_awarded_marks = min(
        total_awarded_marks,
        question.marks
    )


    # ------------------------------------------------------
    # TOTAL TESTS
    # ------------------------------------------------------

    total_tests = test_cases.count()


    # ------------------------------------------------------
    # OVERALL STATUS
    # ------------------------------------------------------

    if passed_tests == total_tests:

        overall_status = "PASSED"

        overall_feedback = (
            f"All {total_tests} "
            "test cases passed."
        )

    elif passed_tests > 0:

        overall_status = "PARTIAL"

        overall_feedback = (
            f"{passed_tests} of "
            f"{total_tests} test cases passed."
        )

    else:

        overall_status = "FAILED"

        overall_feedback = (
            "No test cases passed."
        )


    # ------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------

    return {

        "marks":
            total_awarded_marks,

        "max_marks":
            question.marks,

        "passed":
            passed_tests,

        "total_tests":
            total_tests,

        "feedback":
            overall_feedback,

        "status":
            overall_status,

        "test_results":
            test_results,

    }