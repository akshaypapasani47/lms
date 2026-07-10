
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def default_expiry():
    return timezone.now() + timedelta(days=30)

class VirtualLabUser(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    linux_username = models.CharField(
        max_length=100,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expiry_date = models.DateTimeField(
        default=default_expiry
    )

    is_disabled = models.BooleanField(
        default=False
    )
    
    def __str__(self):
        return self.linux_username

class LabAccount(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    linux_username = models.CharField(
        max_length=100,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.linux_username

from django.db import models

class ActiveSession(models.Model):

    username = models.CharField(
        max_length=100,
        #unique=True
    )

    login_time = models.DateTimeField(
        auto_now_add=True
    )

    logout_time = models.DateTimeField(
        null=True,
        blank=True
    )

    last_activity = models.DateTimeField(
        null=True,
        blank=True
    )

    
    active = models.BooleanField(
        default=True
    )

    def __str__(self):

        return self.username