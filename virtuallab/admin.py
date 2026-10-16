
from django.contrib import admin
from .models import VirtualLabDockerEnvironment
from .models import (
    VirtualLab,
    VirtualLabAccessRequest,
    StudentLabEnvironment,
    LabSession,
    LabResource,
)


@admin.register(VirtualLab)
class VirtualLabAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "lab_type",
        "technology",
        "status",
        "allocated_ram",
        "allocated_storage",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "lab_type",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "technology",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )


@admin.register(VirtualLabAccessRequest)
class VirtualLabAccessRequestAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "lab",
        "status",
        "requested_at",
        "reviewed_by",
        "reviewed_at",
    )

    list_filter = (
        "status",
        "lab",
        "requested_at",
    )

    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
        "student__email",
        "lab__name",
    )

    readonly_fields = (
        "requested_at",
        "reviewed_at",
    )

    ordering = (
        "-requested_at",
    )


@admin.register(StudentLabEnvironment)
class StudentLabEnvironmentAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "lab",
        "status",
        "container_name",
        "container_id",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "lab",
        "created_at",
    )

    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
        "lab__name",
        "container_name",
        "container_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_started_at",
        "last_stopped_at",
    )

    ordering = (
        "-updated_at",
    )


@admin.register(LabSession)
class LabSessionAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "lab",
        "status",
        "opened_at",
        "last_activity",
        "closed_at",
        "duration_seconds",
    )

    list_filter = (
        "status",
        "lab",
        "opened_at",
    )

    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
        "student__email",
        "lab__name",
    )

    readonly_fields = (
        "opened_at",
        "last_activity",
        "closed_at",
        "duration_seconds",
    )

    ordering = (
        "-opened_at",
    )


@admin.register(LabResource)
class LabResourceAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "lab",
        "resource_type",
        "uploaded_by",
        "is_active",
        "created_at",
    )

    list_filter = (
        "resource_type",
        "is_active",
        "lab",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "lab__name",
        "uploaded_by__username",
        "uploaded_by__first_name",
        "uploaded_by__last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )




@admin.register(VirtualLabDockerEnvironment)
class VirtualLabDockerEnvironmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "environment_type",
        "docker_image",
        "status",
        "default_ram",
        "default_storage",
    )

    list_filter = (
        "environment_type",
        "status",
    )

    search_fields = (
        "name",
        "docker_image",
    )