from django.conf import settings
from django.db import models
from django.utils import timezone
class VirtualLabDockerEnvironment(models.Model):
    ENVIRONMENT_TYPE_CHOICES = (
        ("PROGRAMMING", "Programming"),
        ("AI", "AI / Machine Learning"),
        ("BIG_DATA", "Big Data"),
        ("HPC", "HPC"),
        ("QUANTUM", "Quantum"),
        ("CYBER_SECURITY", "Cyber Security"),
        ("CLOUD", "Cloud"),
    )

    STATUS_CHOICES = (
        ("READY", "Ready"),
        ("COMING_SOON", "Coming Soon"),
        ("INACTIVE", "Inactive"),
    )

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    environment_type = models.CharField(
        max_length=30,
        choices=ENVIRONMENT_TYPE_CHOICES,
    )

    docker_image = models.CharField(
        max_length=255,
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="READY",
    )

    description = models.TextField(
        blank=True,
    )

    default_ram = models.IntegerField(
        default=2048,
        help_text="Default RAM allocation in MB.",
    )

    default_storage = models.IntegerField(
        default=10240,
        help_text="Default storage allocation in MB.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["environment_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.docker_image})"

class VirtualLab(models.Model):

    LAB_TYPE_CHOICES = (
        ("PROGRAMMING", "Programming Lab"),
        ("AI", "AI Lab"),
        ("BIG_DATA", "Big Data Lab"),
        ("QUANTUM", "Quantum Lab"),
        ("HPC", "HPC Lab"),
        ("CYBER_SECURITY", "Cyber Security Lab"),
        ("CLOUD", "Cloud Lab"),
    )

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("ARCHIVED", "Archived"),
    )

    name = models.CharField(
        max_length=150
    )

    docker_environment = models.ForeignKey(
        "VirtualLabDockerEnvironment",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="labs",
    )

    lab_type = models.CharField(
        max_length=50,
        choices=LAB_TYPE_CHOICES
    )

    description = models.TextField(
        blank=True
    )

    technology = models.CharField(
        max_length=150,
        blank=True
    )

    allocated_ram = models.IntegerField(
        default=2048,
        help_text="RAM allocation in MB."
    )

    allocated_storage = models.IntegerField(
        default=10240,
        help_text="Storage allocation in MB."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )



    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="virtuallab_created_labs"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(
                fields=["status"]
            ),
            models.Index(
                fields=["lab_type", "status"]
            ),
        ]

    def __str__(self):
        return self.name


class VirtualLabAccessRequest(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    )

    lab = models.ForeignKey(
        VirtualLab,
        on_delete=models.CASCADE,
        related_name="access_requests"
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="virtual_lab_access_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    is_active = models.BooleanField(
        default=True
    )

    requested_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_virtual_lab_requests"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    review_reason = models.TextField(
        blank=True
    )

    class Meta:

        ordering = [
            "-requested_at"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "lab",
                    "student"
                ],
                condition=models.Q(
                    status="PENDING"
                ),
                name="unique_pending_virtual_lab_request"
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "lab",
                    "status"
                ]
            ),
            models.Index(
                fields=[
                    "student",
                    "status"
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.student.username} → "
            f"{self.lab.name} ({self.status})"
        )


class StudentLabEnvironment(models.Model):

    STATUS_CHOICES = (
        ("PROVISIONING", "Provisioning"),
        ("READY", "Ready"),
        ("RUNNING", "Running"),
        ("STOPPED", "Stopped"),
        ("ERROR", "Error"),
        ("DELETED", "Deleted"),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="virtual_lab_environments"
    )

    lab = models.ForeignKey(
        VirtualLab,
        on_delete=models.CASCADE,
        related_name="student_environments"
    )

    container_name = models.CharField(
        max_length=200,
        blank=True
    )

    container_id = models.CharField(
        max_length=200,
        blank=True
    )

    workspace_path = models.CharField(
        max_length=500,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PROVISIONING"
    )

    
    jupyter_token = models.CharField(
        max_length=128,
        blank=True,
        default="",
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    last_started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    last_stopped_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "lab"
                ],
                name="unique_student_virtual_lab_environment"
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "student",
                    "lab"
                ]
            ),
            models.Index(
                fields=[
                    "status"
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.lab.name}"
        )


class LabSession(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("CLOSED", "Closed"),
        ("TIMEOUT", "Timed Out"),
        ("FORCED_CLOSED", "Force Closed"),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="virtual_lab_sessions"
    )

    lab = models.ForeignKey(
        VirtualLab,
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    environment = models.ForeignKey(
        StudentLabEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    opened_at = models.DateTimeField(
        auto_now_add=True
    )

    last_activity = models.DateTimeField(
        default=timezone.now
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    duration_seconds = models.PositiveIntegerField(
        default=0
    )

    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    class Meta:

        ordering = [
            "-opened_at"
        ]

        indexes = [
            models.Index(
                fields=[
                    "student",
                    "status"
                ]
            ),
            models.Index(
                fields=[
                    "lab",
                    "status"
                ]
            ),
            models.Index(
                fields=[
                    "opened_at"
                ]
            ),
            models.Index(
                fields=[
                    "last_activity"
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.lab.name} - "
            f"{self.status}"
        )

    @property
    def is_active(self):
        return self.status == "ACTIVE"

    def calculate_duration(self):

        end_time = (
            self.closed_at
            or timezone.now()
        )

        duration = (
            end_time - self.opened_at
        )

        return max(
            0,
            int(duration.total_seconds())
        )


class LabResource(models.Model):

    RESOURCE_TYPE_CHOICES = (
        ("FILE", "File"),
        ("PDF", "PDF"),
        ("DATASET", "Dataset"),
        ("CODE", "Code"),
        ("DOCUMENT", "Document"),
        ("OTHER", "Other"),
    )

    lab = models.ForeignKey(
        VirtualLab,
        on_delete=models.CASCADE,
        related_name="resources"
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default="FILE"
    )

    file = models.FileField(
        upload_to="virtual_lab_resources/%Y/%m/"
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_virtual_lab_resources"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(
                fields=[
                    "lab",
                    "is_active"
                ]
            ),
            models.Index(
                fields=[
                    "resource_type"
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.title} - "
            f"{self.lab.name}"
        )