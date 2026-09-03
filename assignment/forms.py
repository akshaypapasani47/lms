from django import forms
from .models import Assignment, AssignmentQuestion, TestCase

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = [
            "title",
            "description",
            "virtual_lab",
            "status",
            "start_date",
            "due_date",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "virtual_lab": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "due_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }


class AssignmentQuestionForm(forms.ModelForm):
    class Meta:
        model = AssignmentQuestion
        fields = [
            "question_number",
            "question_text",
            "question_type",
            "marks",
            "programming_language",
            "order",
        ]
        widgets = {
            "question_number": forms.NumberInput(attrs={"class": "form-control"}),
            "question_text": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "question_type": forms.Select(attrs={"class": "form-select"}),
            "marks": forms.NumberInput(attrs={"class": "form-control"}),
            "programming_language": forms.TextInput(attrs={"class": "form-control", "placeholder": "PYTHON, JAVA, CPP"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }



class TestCaseForm(forms.ModelForm):
    # Set required=False so backend validation doesn't block dynamic JS input population
    input_data = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "id": "id_input_data"}),
        required=False
    )

    class Meta:
        model = TestCase
        fields = [
            "input_data",
            "expected_output",
            "marks",
            "is_hidden",
            "order",
        ]
        widgets = {
            "expected_output": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "marks": forms.NumberInput(attrs={"class": "form-control"}),
            "is_hidden": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }