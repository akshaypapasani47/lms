from .programming_evaluator import (
    evaluate_programming_question
)


class FakeTestCase:

    def __init__(
        self,
        input_data,
        expected_output,
        marks,
        order=1,
        is_hidden=False,
    ):

        self.id = order
        self.input_data = input_data
        self.expected_output = expected_output
        self.marks = marks
        self.order = order
        self.is_hidden = is_hidden


class FakeTestCases:

    def __init__(self, cases):
        self.cases = cases

    def all(self):
        return self

    def order_by(self, field):
        return self

    def exists(self):
        return bool(self.cases)

    def count(self):
        return len(self.cases)

    def __iter__(self):
        return iter(self.cases)


class FakeQuestion:

    def __init__(self):

        self.language = "PYTHON"
        self.marks = 10

        self.test_cases = FakeTestCases(
            [
                FakeTestCase(
                    input_data="2 3\n",
                    expected_output="5\n",
                    marks=5,
                    order=1,
                ),

                FakeTestCase(
                    input_data="10 20\n",
                    expected_output="30\n",
                    marks=5,
                    order=2,
                ),
            ]
        )


question = FakeQuestion()

code = """
a, b = map(int, input().split())
print(a + b)
"""

result = evaluate_programming_question(
    question,
    code,
)

print("RESULT")
print(result)