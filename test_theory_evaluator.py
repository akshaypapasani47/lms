import os

import django


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()


from assessment.evaluator.theory_evaluator import (
    evaluate_theory_answer,
)


result = evaluate_theory_answer(
    question_text="What is a primary key in a database?",

    student_answer=(
        "A primary key is a column that uniquely "
        "identifies each record in a table."
    ),

    max_marks=5,

    reference_answer=(
        "A primary key uniquely identifies each row "
        "in a table. It must contain unique values "
        "and cannot contain NULL values."
    ),

    evaluation_criteria=[
        "Definition of primary key",
        "Uniquely identifies a record",
        "No duplicate values",
        "Cannot contain NULL values",
    ],
)


print("\n==============================")
print("THEORY EVALUATOR TEST")
print("==============================")

print("Marks:", result["marks"])
print("Max Marks:", result["max_marks"])
print("Correct:", result["is_correct"])
print("Status:", result["status"])
print("Feedback:", result["feedback"])