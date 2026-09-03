from . import get_runner


def evaluate_code(
    question,
    submitted_code
):

    runner = get_runner(
        question.language
    )

    test_cases = (
        question.test_cases
        .all()
        .order_by("order")
    )

    results = []

    total_test_marks = 0
    obtained_test_marks = 0

    for test_case in test_cases:

        total_test_marks += test_case.marks

        execution = runner.run(
            code=submitted_code,
            input_data=test_case.input_data or ""
        )

        passed = False

        if execution.status == "SUCCESS":

            passed = runner.outputs_match(
                execution.output,
                test_case.expected_output
            )

        awarded_marks = (
            test_case.marks
            if passed
            else 0
        )

        obtained_test_marks += awarded_marks

        results.append({

            "test_case_id": test_case.id,

            "passed": passed,

            "status": execution.status,

            "marks": test_case.marks,

            "awarded_marks": awarded_marks,

            "execution_time": execution.execution_time,

            "error": execution.error,

            "timed_out": execution.timed_out,

            "compile_error": execution.compile_error,

            "is_hidden": test_case.is_hidden,

            # Never expose hidden test case details
            "input": (
                test_case.input_data
                if not test_case.is_hidden
                else None
            ),

            "expected_output": (
                test_case.expected_output
                if not test_case.is_hidden
                else None
            ),

            "actual_output": (
                execution.output
                if not test_case.is_hidden
                else None
            ),

        })

    # ------------------------------------------------------
    # Convert test-case marks to question marks
    # ------------------------------------------------------

    if total_test_marks > 0:

        marks_awarded = (
            obtained_test_marks
            / total_test_marks
        ) * question.marks

    else:

        marks_awarded = 0

    marks_awarded = min(
        round(marks_awarded, 2),
        question.marks
    )

    return {

        "question_marks": question.marks,

        "total_test_marks": total_test_marks,

        "raw_marks_awarded": obtained_test_marks,

        "marks_awarded": marks_awarded,

        "passed_tests": sum(
            1
            for result in results
            if result["passed"]
        ),

        "total_tests": len(results),

        "tests": results,

    }