from django.contrib import admin
from .models import (
    Assignment,
    AssignmentQuestion,
    TestCase,
    StudentSubmission,
    QuestionSubmission,
)


class AssignmentQuestionInline(admin.TabularInline):
    model = AssignmentQuestion
    extra = 1


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "virtual_lab",
        "created_by",
        "status",
        "total_marks",
        "due_date",
        "created_at",
    )
    list_filter = (
        "status",
        "virtual_lab",
    )
    search_fields = (
        "title",
        "description",
    )
    inlines = [AssignmentQuestionInline]


@admin.register(AssignmentQuestion)
class AssignmentQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "question_number",
        "question_type",
        "programming_language",
        "marks",
        "order",
    )
    list_filter = (
        "question_type",
        "programming_language",
    )
    search_fields = (
        "question_text",
    )
    inlines = [TestCaseInline]


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "marks",
        "is_hidden",
        "order",
    )
    list_filter = (
        "is_hidden",
    )


admin.site.register(StudentSubmission)
admin.site.register(QuestionSubmission)