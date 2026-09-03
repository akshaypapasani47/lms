from django.db import models
from django.conf import settings


class Assessment(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("PUBLISHED", "Published"),
        ("CLOSED", "Closed"),
    )

    title = models.CharField(max_length=200)

    description = models.TextField(
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assessments"
    )

    total_marks = models.PositiveIntegerField(
        default=0
    )

    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Assessment duration in minutes."
    )

    start_date = models.DateTimeField(
        null=True,
        blank=True
    )

    due_date = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    allow_multiple_attempts = models.BooleanField(
        default=False
    )

    max_attempts = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class AssessmentQuestion(models.Model):

    QUESTION_TYPES = (
        ("MCQ", "Multiple Choice"),
        ("MULTIPLE_SELECT", "Multiple Select"),
        ("FILL_BLANK", "Fill in the Blank"),
        ("THEORY", "Theory"),
        ("PROGRAMMING", "Programming"),
    )

    LANGUAGE_CHOICES = (
        ("PYTHON", "Python"),
        ("JAVA", "Java"),
        ("C", "C"),
        ("CPP", "C++"),
    )

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()

    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPES
    )

    marks = models.PositiveIntegerField(
        default=1
    )

    order = models.PositiveIntegerField(
        default=1
    )

    # Used only for programming questions
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        null=True,
        blank=True
    )

    # Programming question information
    input_description = models.TextField(
        blank=True,
        null=True
    )

    output_description = models.TextField(
        blank=True,
        null=True
    )

    constraints = models.TextField(
        blank=True,
        null=True
    )

    # Used for theory/AI evaluation
    reference_answer = models.TextField(
        blank=True,
        null=True
    )

    evaluation_criteria = models.JSONField(
        default=list,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}"


class QuestionOption(models.Model):

    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="options"
    )

    option_text = models.TextField()

    is_correct = models.BooleanField(
        default=False
    )

    order = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return self.option_text


class TestCase(models.Model):

    COMPARISON_CHOICES = (
        ("EXACT", "Exact"),
        ("WHITESPACE", "Ignore Whitespace"),
        ("NUMERIC", "Numeric"),
        ("FLOAT", "Floating Point"),
        ("UNORDERED", "Unordered"),
    )

    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="test_cases"
    )

    input_data = models.TextField(
        blank=True,
        null=True
    )

    expected_output = models.TextField()

    is_hidden = models.BooleanField(
        default=True
    )

    marks = models.PositiveIntegerField(
        default=0
    )

    order = models.PositiveIntegerField(
        default=1
    )

    comparison_type = models.CharField(
        max_length=20,
        choices=COMPARISON_CHOICES,
        default="WHITESPACE"
    )

    tolerance = models.FloatField(
        default=0.000001,
        help_text="Used for floating-point comparison."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Test Case {self.order} - {self.question}"


class AssessmentPlacement(models.Model):

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="placements"
    )

    course = models.ForeignKey(
        "course.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assessment_placements"
    )

    module = models.ForeignKey(
        "course.Module",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assessment_placements"
    )

    chapter = models.ForeignKey(
        "course.Chapter",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assessment_placements"
    )

    lesson = models.ForeignKey(
        "course.Lesson",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assessment_placements"
    )

    virtual_lab = models.ForeignKey(
        "programming_lab.VirtualLab",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assessment_placements"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.assessment.title} placement"


class AssessmentSubmission(models.Model):

    STATUS_CHOICES = (
        ("IN_PROGRESS", "In Progress"),
        ("SUBMITTED", "Submitted"),
        ("EVALUATED", "Evaluated"),
    )

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_submissions"
    )

    attempt_number = models.PositiveIntegerField(
        default=1
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="IN_PROGRESS"
    )

    total_marks = models.FloatField(
        default=0
    )

    def __str__(self):
        return f"{self.student.username} - {self.assessment.title}"


class QuestionSubmission(models.Model):

    submission = models.ForeignKey(
        AssessmentSubmission,
        on_delete=models.CASCADE,
        related_name="question_submissions"
    )

    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    # Used for MCQ / fill blank / theory
    answer_text = models.TextField(
        blank=True,
        null=True
    )

    # Used for programming
    submitted_code = models.TextField(
        blank=True,
        null=True
    )

    marks_awarded = models.FloatField(
        default=0
    )

    is_correct = models.BooleanField(
        null=True,
        blank=True
    )

    feedback = models.TextField(
        blank=True,
        null=True
    )

    evaluated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.submission.student.username} - Q{self.question.order}"