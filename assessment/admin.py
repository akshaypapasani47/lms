from django.contrib import admin

from .models import (
    Assessment,
    AssessmentQuestion,
    QuestionOption,
    TestCase,
    AssessmentPlacement,
    AssessmentSubmission,
    QuestionSubmission,
)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 2


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 2


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):

    list_display = (
        "assessment",
        "order",
        "question_type",
        "marks",
        "language",
    )

    list_filter = (
        "question_type",
        "language",
    )

    ordering = (
        "assessment",
        "order",
    )

    inlines = [
        QuestionOptionInline,
        TestCaseInline,
    ]


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "created_by",
        "total_marks",
        "status",
        "start_date",
        "due_date",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "title",
        "description",
    )

    ordering = (
        "-created_at",
    )


@admin.register(AssessmentPlacement)
class AssessmentPlacementAdmin(admin.ModelAdmin):

    list_display = (
        "assessment",
        "course",
        "module",
        "chapter",
        "lesson",
        "virtual_lab",
    )

    list_filter = (
        "course",
        "virtual_lab",
    )


@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):

    list_display = (
        "assessment",
        "student",
        "attempt_number",
        "status",
        "total_marks",
        "started_at",
        "submitted_at",
    )

    list_filter = (
        "status",
        "assessment",
    )

    search_fields = (
        "student__username",
        "assessment__title",
    )


@admin.register(QuestionSubmission)
class QuestionSubmissionAdmin(admin.ModelAdmin):

    list_display = (
        "submission",
        "question",
        "marks_awarded",
        "is_correct",
        "evaluated_at",
    )

    list_filter = (
        "is_correct",
    )