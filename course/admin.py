from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Program, Course, CourseAllocation, Upload, VideoWatchProgress
from modeltranslation.admin import TranslationAdmin
from .models import Module, Chapter, Lesson

class ProgramAdmin(TranslationAdmin):
    pass
class CourseAdmin(TranslationAdmin):
    pass
class UploadAdmin(TranslationAdmin):
    pass

admin.site.register(Program, ProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseAllocation)
admin.site.register(Upload, UploadAdmin)
admin.site.register(Module)
admin.site.register(Chapter)
admin.site.register(Lesson)


@admin.register(VideoWatchProgress)
class VideoWatchProgressAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "video",
        "progress_percent",
        "position_seconds",
        "updated_at",
    )
    list_filter = ("completed",)
    search_fields = ("video__title", "student__student__username")
    raw_id_fields = ("student", "video")
    readonly_fields = ("created_at", "updated_at")
