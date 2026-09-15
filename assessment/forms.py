from django import forms

from .models import (
    Assessment,
    AssessmentQuestion,
    QuestionOption,
    TestCase,
    AssessmentPlacement,
)

class AssessmentForm(forms.ModelForm):

    class Meta:
        model = Assessment

        fields = [
            "title",
            "description",
            "total_marks",
            "duration_minutes",
            "start_date",
            "due_date",
            "allow_multiple_attempts",
            "max_attempts",
            "status",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter assessment title",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),

            "total_marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "duration_minutes": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "start_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),

            "due_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),

            "max_attempts": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }


class AssessmentQuestionForm(forms.ModelForm):

    class Meta:
        model = AssessmentQuestion

        fields = [
            "question_text",
            "question_type",
            "marks",
            "ai_evaluation_marks",
            "order",
            "language",
            "input_description",
            "output_description",
            "constraints",
            "example_input",
            "example_output",
            "reference_answer",
            "evaluation_criteria",
        ]

        widgets = {

            "question_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter the question..."
                }
            ),

            "question_type": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_question_type"
                }
            ),

            "marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1
                }
            ),

            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1
                }
            ),

            "language": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "input_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe the input..."
                }
            ),

            "output_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe the expected output..."
                }
            ),

            "constraints": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Example: 1 <= n <= 1000"
                }
            ),

            "example_input": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Enter example input exactly as "
                        "the program should receive it.\n\n"
                        "Example:\n"
                        "10 20"
                    ),
                }
            ),

            "example_output": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Enter the expected output for the "
                        "example input.\n\n"
                        "Example:\n"
                        "30"
                    ),
                }
            ),

            "reference_answer": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter the reference/correct answer..."
                }
            ),

            "evaluation_criteria": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Correct concept - 4\n"
                        "Explanation - 3\n"
                        "Example - 3"
                    )
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["language"].required = False
        self.fields["input_description"].required = False
        self.fields["output_description"].required = False
        self.fields["constraints"].required = False
        self.fields["example_input"].required = False
        self.fields["example_output"].required = False
        self.fields["reference_answer"].required = False
        self.fields["evaluation_criteria"].required = False


class QuestionOptionForm(forms.ModelForm):

    class Meta:
        model = QuestionOption

        fields = [
            "option_text",
            "is_correct",
            "order",
        ]

        widgets = {

            "option_text": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter option"
                }
            ),

            "is_correct": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),

            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1
                }
            ),
        }


class TestCaseForm(forms.ModelForm):

    class Meta:
        model = TestCase

        fields = [
            "input_data",
            "expected_output",
            "comparison_type",
            "tolerance",
            "is_hidden",
            "marks",
        ]

        widgets = {

            # ==================================================
            # INPUT
            # ==================================================

            "input_data": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": (
                        "Enter complete input exactly as "
                        "the program should receive it.\n\n"
                        "Example:\n"
                        "2\n"
                        "10 20\n\n"
                        "The input format depends on the "
                        "programming question."
                    ),
                }
            ),

            # ==================================================
            # EXPECTED OUTPUT
            # ==================================================

            "expected_output": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": (
                        "Enter expected output.\n\n"
                        "Example:\n"
                        "30"
                    ),
                }
            ),

            # ==================================================
            # COMPARISON TYPE
            # ==================================================

            "comparison_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            # ==================================================
            # FLOATING POINT TOLERANCE
            # ==================================================

            "tolerance": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "any",
                    "min": "0",
                    "placeholder": (
                        "Example: 0.000001"
                    ),
                }
            ),

            # ==================================================
            # HIDDEN TEST CASE
            # ==================================================

            "is_hidden": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),

            # ==================================================
            # MARKS
            # ==================================================

            "marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["comparison_type"].label = (
            "Output Comparison"
        )

        self.fields["comparison_type"].help_text = (
            "Choose how the student's output should "
            "be compared with the expected output."
        )

        self.fields["tolerance"].label = (
            "Floating Point Tolerance"
        )

        self.fields["tolerance"].help_text = (
            "Used only when Floating Point comparison "
            "is selected. Example: 0.000001"
        )

        self.fields["tolerance"].required = False
        self.fields["tolerance"].initial = 0.000001


    def clean_tolerance(self):
        tolerance = self.cleaned_data.get("tolerance")

        if tolerance is None:
            return 0.000001

        return tolerance


# ==========================================================
# ASSESSMENT PLACEMENT FORM
# ==========================================================

class AssessmentPlacementForm(forms.ModelForm):

    class Meta:
        from .models import AssessmentPlacement

        model = AssessmentPlacement

        fields = [
            "course",
            "module",
            "chapter",
            "lesson",
            "virtual_lab",
        ]

        widgets = {

            "course": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "module": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "chapter": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "lesson": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "virtual_lab": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),
        }