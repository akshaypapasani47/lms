from django.db import models
from django.conf import settings
from programming_lab.models import VirtualLab


class Assignment(models.Model):
    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("PUBLISHED", "Published"),
        ("CLOSED", "Closed"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    virtual_lab = models.ForeignKey(
        VirtualLab,
        on_delete=models.CASCADE,
        related_name="assignments",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assignments",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )
    total_marks = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def update_total_marks(self):
        """Recalculates total marks whenever a question is added or modified."""
        total = self.questions.aggregate(models.Sum("marks"))["marks__sum"] or 0
        self.total_marks = total
        self.save(update_fields=["total_marks"])


class AssignmentQuestion(models.Model):
    QUESTION_TYPE_CHOICES = (
        ("PROGRAMMING", "Programming"),
        ("MCQ", "Multiple Choice"),
        ("FILL_BLANK", "Fill in the Blank"),
        ("DESCRIPTIVE", "Descriptive"),
    )

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_number = models.PositiveIntegerField(default=1)
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPE_CHOICES,
        default="PROGRAMMING",
    )
    marks = models.PositiveIntegerField(default=1)
    programming_language = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="e.g., PYTHON, JAVA, CPP, C",
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "question_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "question_number"],
                name="unique_assignment_question_number",
            )
        ]

    def __str__(self):
        return f"{self.assignment.title} - Q{self.question_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.assignment.update_total_marks()


class TestCase(models.Model):
    question = models.ForeignKey(
        AssignmentQuestion,
        on_delete=models.CASCADE,
        related_name="test_cases",
    )
    input_data = models.TextField(blank=True)
    expected_output = models.TextField()
    marks = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def get_input_list(self):
        """Splits input string by lines into a clean list of inputs."""
        if not self.input_data:
            return []
        return [line.strip() for line in self.input_data.strip().splitlines() if line.strip()]    

    def __str__(self):
        return f"Test Case Q{self.question.question_number} - {self.question.assignment.title}"


class StudentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    obtained_marks = models.PositiveIntegerField(default=0)
    ai_feedback = models.TextField(blank=True, null=True)
    is_evaluated = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


class QuestionSubmission(models.Model):
    submission = models.ForeignKey(
        StudentSubmission,
        on_delete=models.CASCADE,
        related_name="question_answers",
    )
    question = models.ForeignKey(
        AssignmentQuestion,
        on_delete=models.CASCADE,
    )
    submitted_code = models.TextField(blank=True)
    obtained_marks = models.PositiveIntegerField(default=0)
    execution_output = models.TextField(blank=True)
    ai_analysis = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Q{self.question.question_number} Answer by {self.submission.student.username}"