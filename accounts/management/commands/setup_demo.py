"""
Create demo admin, one lecturer, five students, plus minimal program/course/session data.

Passwords are set before the first save so the accounts signal does not replace
usernames/passwords. Safe to re-run: refreshes passwords and role flags.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User, Student
from core.models import Session, Semester
from course.models import Program, Course, CourseAllocation
from result.models import TakenCourse


def _ensure_user(username: str, password: str, **fields) -> User:
    """Create or update a user; password is always reset to the given value."""
    user = User.objects.filter(username=username).first()
    if user:
        for key, value in fields.items():
            setattr(user, key, value)
        user.set_password(password)
        user.save()
        return user

    user = User(username=username, **fields)
    user.set_password(password)
    user.save()
    return user


class Command(BaseCommand):
    help = (
        "Create demo users (1 admin, 1 lecturer, 5 students) and sample course data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-password",
            default="AdminDemo123!",
            help="Password for the admin user",
        )
        parser.add_argument(
            "--lecturer-password",
            default="LecturerDemo123!",
            help="Password for the lecturer user",
        )
        parser.add_argument(
            "--student-password",
            default="StudentDemo123!",
            help="Password for each demo student account",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin_pw = options["admin_password"]
        lec_pw = options["lecturer_password"]
        stu_pw = options["student_password"]

        session, _ = Session.objects.get_or_create(
            session="2025-2026",
            defaults={"is_current_session": True},
        )
        Session.objects.exclude(pk=session.pk).update(is_current_session=False)
        session.is_current_session = True
        session.save(update_fields=["is_current_session"])

        semester, _ = Semester.objects.get_or_create(
            semester="First",
            session=session,
            defaults={
                "is_current_semester": True,
            },
        )
        Semester.objects.exclude(pk=semester.pk).update(is_current_semester=False)
        semester.is_current_semester = True
        semester.session = session
        semester.save(update_fields=["is_current_semester", "session"])

        program, _ = Program.objects.get_or_create(
            title="Computer Science",
            defaults={"summary": "Demo program for local LMS testing."},
        )

        course, _ = Course.objects.get_or_create(
            code="CS101",
            defaults={
                "title": "Introduction to Programming",
                "summary": "Demo course — upload videos and materials here.",
                "program": program,
                "level": "Bachelor Degree",
                "year": 1,
                "semester": "First",
            },
        )
        if course.program_id != program.id:
            course.program = program
            course.save(update_fields=["program"])

        admin = _ensure_user(
            "admin",
            admin_pw,
            email="admin@example.com",
            first_name="Site",
            last_name="Admin",
            is_staff=True,
            is_superuser=True,
            is_lecturer=False,
            is_student=False,
        )

        lecturer = _ensure_user(
            "lecturer",
            lec_pw,
            email="lecturer@example.com",
            first_name="Demo",
            last_name="Lecturer",
            is_staff=False,
            is_superuser=False,
            is_lecturer=True,
            is_student=False,
        )

        student_defs = [
            ("student01", "One", "M"),
            ("student02", "Two", "F"),
            ("student03", "Three", "M"),
            ("student04", "Four", "F"),
            ("student05", "Five", "M"),
        ]

        for username, suffix, gender in student_defs:
            student_user = _ensure_user(
                username,
                stu_pw,
                email=f"{username}@example.com",
                first_name="Student",
                last_name=suffix,
                is_staff=False,
                is_superuser=False,
                is_lecturer=False,
                is_student=True,
                gender=gender,
            )
            profile, _ = Student.objects.get_or_create(
                student=student_user,
                defaults={
                    "level": "Bachelor Degree",
                    "program": program,
                },
            )
            if profile.program_id != program.id:
                profile.program = program
            if not profile.level:
                profile.level = "Bachelor Degree"
            profile.save()
            TakenCourse.objects.get_or_create(student=profile, course=course)

        alloc, _ = CourseAllocation.objects.get_or_create(lecturer=lecturer)
        if not alloc.courses.filter(pk=course.pk).exists():
            alloc.courses.add(course)
        if alloc.session_id != session.id:
            alloc.session = session
            alloc.save(update_fields=["session"])

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("")
        lang = settings.LANGUAGE_CODE.rstrip("/")
        self.stdout.write(
            f"Sign in at: /{lang}/accounts/login/ (other languages use their prefix)"
        )
        self.stdout.write("")
        self.stdout.write("--- Login: ID Number = username, then password ---")
        self.stdout.write(f"  Admin:     admin / {admin_pw}")
        self.stdout.write(f"  Lecturer:  lecturer / {lec_pw}")
        for username, _, _ in student_defs:
            self.stdout.write(f"  Student:   {username} / {stu_pw}")
        self.stdout.write("")
        self.stdout.write(
            f"Dashboard (/{lang}/dashboard/) is only for superusers; use the admin account."
        )
        self.stdout.write(f"Sample course slug: {course.slug}")
