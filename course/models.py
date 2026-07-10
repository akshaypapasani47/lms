from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db.models.signals import pre_save, post_save, post_delete
from django.db.models import Q
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from django.core.files import File
import os
import whisper

from .utils import generate_subtitles

# project import
from .utils import *
from core.models import ActivityLog
from django.conf import settings

YEARS = (
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (4, "5"),
    (4, "6"),
)

# LEVEL_COURSE = "Level course"
BACHELOR_DEGREE = _("Bachelor")
MASTER_DEGREE = _("Master")

LEVEL = (
    # (LEVEL_COURSE, "Level course"),
    (BACHELOR_DEGREE, _("Bachelor Degree")),
    (MASTER_DEGREE, _("Master Degree")),
)

FIRST = _("First")
SECOND = _("Second")
THIRD = _("Third")

SEMESTER = (
    (FIRST, _("First")),
    (SECOND, _("Second")),
    (THIRD, _("Third")),
)


class ProgramManager(models.Manager):
    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            or_lookup = Q(title__icontains=query) | Q(summary__icontains=query)
            queryset = queryset.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return queryset


class Program(models.Model):
    title = models.CharField(max_length=150, unique=True)
    summary = models.TextField(null=True, blank=True)

    objects = ProgramManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("program_detail", kwargs={"pk": self.pk})


@receiver(post_save, sender=Program)
def log_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    ActivityLog.objects.create(message=_(f"The program '{instance}' has been {verb}."))


@receiver(post_delete, sender=Program)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(message=_(f"The program '{instance}' has been deleted."))


class CourseManager(models.Manager):
    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            or_lookup = (
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(code__icontains=query)
                | Q(slug__icontains=query)
            )
            queryset = queryset.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return queryset


class Course(models.Model):
    slug = models.SlugField(blank=True, unique=True)
    title = models.CharField(max_length=200, null=True)
    code = models.CharField(max_length=200, unique=True, null=True)
    credit = models.IntegerField(null=True, default=0)
    summary = models.TextField(max_length=200, blank=True, null=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    level = models.CharField(max_length=25, choices=LEVEL, null=True)
    year = models.IntegerField(choices=YEARS, default=0)
    semester = models.CharField(choices=SEMESTER, max_length=200)
    is_elective = models.BooleanField(default=False, blank=True, null=True)
    duration = models.PositiveIntegerField(default=0)
    objects = CourseManager()

    @property
    def duration_display(self):
        hours = self.duration // 3600
        mins = (self.duration % 3600) // 60
        return f"{hours}h {mins}m"

    def __str__(self):
        return "{0} ({1})".format(self.title, self.code)

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})

    @property
    def is_current_semester(self):
        from core.models import Semester

        current_semester = Semester.objects.get(is_current_semester=True)

        if self.semester == current_semester.semester:
            return True
        else:
            return False


def course_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


pre_save.connect(course_pre_save_receiver, sender=Course)


@receiver(post_save, sender=Course)
def log_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    ActivityLog.objects.create(message=_(f"The course '{instance}' has been {verb}."))


@receiver(post_delete, sender=Course)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(message=_(f"The course '{instance}' has been deleted."))


class CourseAllocation(models.Model):
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=_("allocated_lecturer"),
    )
    courses = models.ManyToManyField(Course, related_name=_("allocated_course"))
    session = models.ForeignKey(
        "core.Session", on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.lecturer.get_full_name

    def get_absolute_url(self):
        return reverse("edit_allocated_course", kwargs={"pk": self.pk})


class Upload(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(
        upload_to="course_files/",
        help_text="Valid Files: pdf, docx, doc, xls, xlsx, ppt, pptx, zip, rar, 7zip",
        validators=[
            FileExtensionValidator(
                [
                    "pdf",
                    "docx",
                    "doc",
                    "xls",
                    "xlsx",
                    "ppt",
                    "pptx",
                    "zip",
                    "rar",
                    "7zip",
                ]
            )
        ],
    )
    updated_date = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    upload_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
    

    def __str__(self):
        return str(self.file)[6:]

    def get_extension_short(self):
        ext = str(self.file).split(".")
        ext = ext[len(ext) - 1]

        if ext in ("doc", "docx"):
            return "word"
        elif ext == "pdf":
            return "pdf"
        elif ext in ("xls", "xlsx"):
            return "excel"
        elif ext in ("ppt", "pptx"):
            return "powerpoint"
        elif ext in ("zip", "rar", "7zip"):
            return "archive"

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)


@receiver(post_save, sender=Upload)
def log_save(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            message=_(
                f"The file '{instance.title}' has been uploaded to the course '{instance.course}'."
            )
        )
    else:
        ActivityLog.objects.create(
            message=_(
                f"The file '{instance.title}' of the course '{instance.course}' has been updated."
            )
        )


@receiver(post_delete, sender=Upload)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(
            f"The file '{instance.title}' of the course '{instance.course}' has been deleted."
        )
    )

LANGUAGE_CHOICES = [
    ("hi", "Hindi"),
    ("te", "Telugu"),
    ("kn", "Kannada"),
]
class UploadVideo(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, null=True, blank=True)
    video = models.FileField(
        upload_to="course_videos/",
        help_text=_("Valid video formats: mp4, mkv, wmv, 3gp, f4v, avi, mp3"),
        validators=[
            FileExtensionValidator(["mp4", "mkv", "wmv", "3gp", "f4v", "avi", "mp3"])
        ],
    )

    selected_languages = models.JSONField(
        default=list,
        blank=True,
        help_text="Languages selected during upload"
    )

    duration = models.PositiveIntegerField(
        default=0,
        help_text="Duration in seconds"
    )

    
    subtitle_en = models.FileField(upload_to='subtitles/', null=True, blank=True)
    subtitle_hi = models.FileField(upload_to='subtitles/', null=True, blank=True)
    subtitle_te = models.FileField(upload_to='subtitles/', null=True, blank=True)
    subtitle_kn = models.FileField(upload_to='subtitles/', null=True, blank=True)

    audio_hi = models.FileField(
        upload_to="audio/",
        blank=True,
        null=True
    )

    audio_te = models.FileField(
        upload_to="audio/",
        blank=True,
        null=True
    )

    audio_kn = models.FileField(
        upload_to="audio/",
        blank=True,
        null=True
    )

    #subtitle_hi = models.FileField(upload_to='subtitles/', null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
    
    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse(
            "video_single", kwargs={"slug": self.course.slug, "video_slug": self.slug}
        )

    def delete(self, *args, **kwargs):
        self.video.delete()
        super().delete(*args, **kwargs)

    
   


# @receiver(post_save, sender=UploadVideo)
# def auto_generate_subtitle(sender, instance, created, **kwargs):

#     # run only when new video is uploaded
#     if created and instance.video:        
#         print("🔥 Generating subtitles...")
        
#         video_path = instance.video.path
#         print("Video path:", video_path)
#         en_vtt = generate_subtitles(video_path)
#         hi_vtt = translate_vtt(en_vtt, "hi")
#         te_vtt = translate_vtt(en_vtt, "te")
#         kn_vtt = translate_vtt(en_vtt, "kn")


#         if os.path.exists(en_vtt):
#             with open(en_vtt, "rb") as f:
#                 instance.subtitle_en.save(
#                     os.path.basename(en_vtt),
#                     File(f),
#                     save=False
#                 )

#         if os.path.exists(hi_vtt):
#             with open(hi_vtt, "rb") as f:
#                 instance.subtitle_hi.save(
#                     os.path.basename(hi_vtt),
#                     File(f),
#                     save=False
#                 )

#         if os.path.exists(te_vtt):
#             with open(te_vtt, "rb") as f:
#                 instance.subtitle_te.save(
#                     os.path.basename(te_vtt),
#                     File(f),
#                     save=False
#                 )

#         if os.path.exists(kn_vtt):
#             with open(kn_vtt, "rb") as f:
#                 instance.subtitle_kn.save(
#                     os.path.basename(kn_vtt),
#                     File(f),
#                     save=False
#                 )

#         instance.save()




def video_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


pre_save.connect(video_pre_save_receiver, sender=UploadVideo)


@receiver(post_save, sender=UploadVideo)
def log_save(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            message=_(
                f"The video '{instance.title}' has been uploaded to the course {instance.course}."
            )
        )
    else:
        ActivityLog.objects.create(
            message=_(
                f"The video '{instance.title}' of the course '{instance.course}' has been updated."
            )
        )


@receiver(post_delete, sender=UploadVideo)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(
            f"The video '{instance.title}' of the course '{instance.course}' has been deleted."
        )
    )


class VideoWatchProgress(models.Model):
    """
    One row per student per video (enforced by DB constraint).
    Stores last playback position for resume and a cached completion percentage.
    """

    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="video_watch_progress",
    )
    video = models.ForeignKey(
        UploadVideo,
        on_delete=models.CASCADE,
        related_name="watch_progress",
    )
    position_seconds = models.FloatField(
        default=0.0,
        help_text=_("Last watched playback time in seconds (HTML5 video currentTime)."),
    )
    duration_seconds = models.FloatField(
        default=0.0,
        help_text=_("Video duration when last reported (for percentage)."),
    )
    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Cached 0–100 for list views and dashboards."),
    )
    completed = models.BooleanField(
        default=False,
        help_text=_("True when the viewer reached ~95% or the 'ended' event."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Video watch progress")
        verbose_name_plural = _("Video watch progress")
        constraints = [
            models.UniqueConstraint(
                fields=["student", "video"],
                name="uniq_student_video_watch_progress",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "video"]),
        ]

    def __str__(self):
        return f"{self.student_id}:{self.video_id} @ {self.position_seconds:.1f}s"


class CourseOffer(models.Model):
    _("""NOTE: Only department head can offer semester courses""")

    dep_head = models.ForeignKey("accounts.DepartmentHead", on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.dep_head)
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    duration = models.PositiveIntegerField(default=0)


    @property
    def duration_display(self):
        hours = self.duration // 3600
        mins = (self.duration % 3600) // 60
        return f"{hours}h {mins}m"

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Chapter(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    duration = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    # video = models.FileField(upload_to='lesson_videos/', blank=True, null=True)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    duration = models.PositiveIntegerField(default=0)

    @property
    def duration_display(self):
        mins = self.duration // 60
        secs = self.duration % 60
        return f"{mins}:{secs:02d}"

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

# class LessonCompletion(models.Model):
#     student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE)
#     completed = models.BooleanField(default=False)
#     # progress = models.FloatField(default=0)
#     # last_time = models.FloatField(default=0)
#     class Meta:
#         unique_together = ('student', 'lesson')

#     def __str__(self):
#         return f"{self.student} - {self.lesson} - {self.completed}"

class LessonProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE
    )

    watched_seconds = models.FloatField(default=0)
    progress_percent = models.FloatField(default=0)

    completed = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f"{self.student} - {self.lesson} ({self.progress_percent}%)"