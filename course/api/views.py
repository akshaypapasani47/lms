"""
JSON API for video watch progress (session auth + CSRF on POST).
"""

from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.models import Student
from course.models import UploadVideo
from course.services import video_progress as progress_service


def _require_student(request: HttpRequest) -> Student | JsonResponse:
    user = request.user
    if not user.is_authenticated or not getattr(user, "is_student", False):
        return JsonResponse({"detail": "Only student accounts can use this API."}, status=403)
    student = Student.objects.filter(student=user).select_related("program").first()
    if student is None:
        return JsonResponse({"detail": "No student profile for this user."}, status=403)
    return student


@login_required
@require_http_methods(["GET", "POST"])
def video_progress(request: HttpRequest) -> JsonResponse:
    """
    GET: ?video_id=<pk> — current saved progress for the logged-in student.
    POST: JSON { video_id, position_seconds, duration_seconds } — upsert progress.
    """
    student = _require_student(request)
    if isinstance(student, JsonResponse):
        return student

    if request.method == "GET":
        video_id = request.GET.get("video_id")
        if not video_id or not str(video_id).isdigit():
            return JsonResponse({"detail": "Query parameter video_id is required."}, status=400)
        video = get_object_or_404(UploadVideo, pk=int(video_id))
        row = progress_service.get_progress(student, video)
        if row is None and not progress_service.student_can_track_video(student, video):
            return JsonResponse(
                {"detail": "You are not enrolled in this course."},
                status=403,
            )
        return JsonResponse(
            {"video_id": video.id, **progress_service.serialize_progress(row)}
        )

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    video_id = payload.get("video_id")
    if video_id is None or not str(video_id).isdigit():
        return JsonResponse({"detail": "Field video_id is required."}, status=400)

    try:
        position_seconds = float(payload.get("position_seconds", 0))
        duration_seconds = float(payload.get("duration_seconds", 0))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "position_seconds and duration_seconds must be numbers."}, status=400)

    if position_seconds < 0 or duration_seconds < 0:
        return JsonResponse({"detail": "Times must be non-negative."}, status=400)

    video = get_object_or_404(UploadVideo, pk=int(video_id))

    try:
        row = progress_service.upsert_video_progress(
            student=student,
            video=video,
            position_seconds=position_seconds,
            duration_seconds=duration_seconds,
        )
    except PermissionError as exc:
        return JsonResponse({"detail": str(exc)}, status=403)

    return JsonResponse(
        {
            "ok": True,
            "video_id": video.id,
            **progress_service.serialize_progress(row),
        },
        status=200,
    )
