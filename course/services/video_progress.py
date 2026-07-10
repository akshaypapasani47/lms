"""
Video watch progress — persistence rules and access checks.

Keeps a single row per (student, video) via update_or_create / UniqueConstraint.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from django.db import transaction

from accounts.models import Student
from course.models import UploadVideo, VideoWatchProgress
from result.models import TakenCourse


def student_can_track_video(student: Student, video: UploadVideo) -> bool:
    """
    Only students enrolled in the course (TakenCourse) may record progress.
    Matches typical LMS enrollment; avoids cross-course ID probing.
    """
    return TakenCourse.objects.filter(student=student, course_id=video.course_id).exists()


def _compute_percent(position: float, duration: float, completed_flag: bool) -> int:
    if completed_flag:
        return 100
    if duration and duration > 0:
        pct = int(round(min(100.0, max(0.0, (position / duration) * 100.0))))
        return pct
    return 0


def _merge_position(
    existing: Optional[float], reported: float, duration: float
) -> Tuple[float, bool]:
    """
    Keep monotonic max watched time (standard resume semantics).
    """
    cap = duration if duration and duration > 0 else None
    high = max(existing or 0.0, max(0.0, reported))
    if cap is not None:
        high = min(high, cap)
    completed = bool(cap and high >= cap * 0.95)
    return high, completed


@transaction.atomic
def upsert_video_progress(
    *,
    student: Student,
    video: UploadVideo,
    position_seconds: float,
    duration_seconds: float,
) -> VideoWatchProgress:
    if not student_can_track_video(student, video):
        raise PermissionError("Student is not enrolled in this course.")

    progress, _created = VideoWatchProgress.objects.get_or_create(
        student=student,
        video=video,
        defaults={
            "position_seconds": 0.0,
            "duration_seconds": 0.0,
            "progress_percent": 0,
            "completed": False,
        },
    )

    merged_pos, completed = _merge_position(
        progress.position_seconds, float(position_seconds), float(duration_seconds)
    )
    if float(duration_seconds) > 0:
        dur = float(duration_seconds)
    else:
        dur = float(progress.duration_seconds or 0.0)

    pct = _compute_percent(merged_pos, dur, completed or progress.completed)

    progress.position_seconds = merged_pos
    progress.duration_seconds = max(progress.duration_seconds or 0.0, dur)
    progress.completed = progress.completed or completed
    progress.progress_percent = max(progress.progress_percent, pct)
    progress.save(
        update_fields=[
            "position_seconds",
            "duration_seconds",
            "progress_percent",
            "completed",
            "updated_at",
        ]
    )
    return progress


def get_progress(student: Student, video: UploadVideo) -> Optional[VideoWatchProgress]:
    if not student_can_track_video(student, video):
        return None
    return (
        VideoWatchProgress.objects.filter(student=student, video=video)
        .only(
            "position_seconds",
            "duration_seconds",
            "progress_percent",
            "completed",
        )
        .first()
    )


def progress_map_for_videos(student: Student, video_ids: list[int]) -> dict[int, int]:
    """video_id -> progress_percent for course list UI."""
    if not video_ids:
        return {}
    rows = VideoWatchProgress.objects.filter(
        student=student, video_id__in=video_ids
    ).values_list("video_id", "progress_percent")
    return {int(vid): int(pct) for vid, pct in rows}


def serialize_progress(row: Optional[VideoWatchProgress]) -> dict[str, Any]:
    if row is None:
        return {
            "position_seconds": 0.0,
            "duration_seconds": 0.0,
            "progress_percent": 0,
            "completed": False,
        }
    return {
        "position_seconds": float(row.position_seconds),
        "duration_seconds": float(row.duration_seconds),
        "progress_percent": int(row.progress_percent),
        "completed": bool(row.completed),
    }
