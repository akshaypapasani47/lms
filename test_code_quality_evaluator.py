from assessment.evaluator.code_quality_evaluator import (
    evaluate_code_quality
)


question = """
Write a program to find the largest element
in an array of integers.
"""


student_code = """
n = int(input())
arr = list(map(int, input().split()))

largest = arr[0]

for i in range(1, n):
    if arr[i] > largest:
        largest = arr[i]

print(largest)
"""


reference_answer = """
n = int(input())
arr = list(map(int, input().split()))

largest = arr[0]

for i in range(1, n):
    if arr[i] > largest:
        largest = arr[i]

print(largest)
"""


result = evaluate_code_quality(
    question_text=question,
    submitted_code=student_code,
    language="PYTHON",
    max_marks=2,
    reference_answer=reference_answer,
)


print("==============================")
print("CODE QUALITY EVALUATOR TEST")
print("==============================")
print("Marks:", result["marks"])
print("Max Marks:", result["max_marks"])
print("Status:", result["status"])
print("Feedback:", result["feedback"])