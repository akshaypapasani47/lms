import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from assessment.evaluator.theory_evaluator import evaluate_theory_answer


result = evaluate_theory_answer(
    question_text="What is a primary key in a database?",
    student_answer=(
        "A primary key is a column or set of columns that "
        "uniquely identifies each record in a table."
    ),
    max_marks=5,
    reference_answer=(
        "A primary key uniquely identifies each row in a table "
        "and cannot contain duplicate values."
    ),
    evaluation_criteria=[
        "Definition of primary key",
        "Uniquely identifies a record",
        "No duplicate values",
    ],
)

print("\n==============================")
print("THEORY AI TEST RESULT")
print("==============================")
print(result)