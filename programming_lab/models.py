from django.db import models
from django.conf import settings
from django.contrib.auth.models import User



class ProgrammingLab(models.Model):

    LANGUAGE_CHOICES = (
        ("PYTHON", "Python"),
        ("JAVA", "Java"),
        ("CPP", "C++"),
    )

    language = models.CharField(
        max_length=50,
        choices=LANGUAGE_CHOICES
    )

    allocated_ram = models.IntegerField(
        default=0
    )

    allocated_storage = models.IntegerField(
        default=0
    )

    status = models.CharField(
        max_length=50,
        default="ACTIVE"
    )

    expiry_date = models.DateTimeField(
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return self.language




class StudentContainer(models.Model):

    user=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    container_name=models.CharField(
        max_length=200
    )

    container_id=models.CharField(
        max_length=200
    )

    status=models.CharField(
        max_length=20,
        default="running"
    )

    created_at=models.DateTimeField(
        auto_now_add=True
    )




class VirtualLab(models.Model):

    LAB_TYPE_CHOICES = (
        ("PROGRAMMING", "Programming Lab"),
        ("AI", "AI Lab"),
        ("BIG_DATA", "Big Data Lab"),
        ("QUANTUM", "Quantum Lab"),
        ("HPC", "HPC Lab"),
    )

    name = models.CharField(
        max_length=150
    )

    lab_type = models.CharField(
        max_length=50,
        choices=LAB_TYPE_CHOICES
    )

    description = models.TextField(
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_virtual_labs"
    )

    status = models.CharField(
        max_length=20,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name



class VirtualLabAccess(models.Model):

    lab = models.ForeignKey(
        VirtualLab,
        on_delete=models.CASCADE,
        related_name="access_permissions"
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="virtual_lab_access"
    )

    is_active = models.BooleanField(
        default=True
    )

    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="granted_lab_permissions"
    )

    granted_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lab", "student"],
                name="unique_virtual_lab_student_access"
            )
        ]

    def __str__(self):
        return f"{self.lab.name} - {self.student.username}"