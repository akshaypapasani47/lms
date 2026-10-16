import io
import base64

import openpyxl
import xlrd
import xlwt

from xlutils.copy import copy as xl_copy

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from .models import (
    VirtualLab,
    VirtualLabAccessRequest,
    StudentLabEnvironment,
    LabSession,
    LabResource,
    VirtualLabDockerEnvironment,
)

from assessment.models import AssessmentPlacement
from .services import (
    VirtualLabAccessService,
    VirtualLabSessionService,
    VirtualLabTerminalService,
)
from pathlib import Path
import json
import os
import subprocess
from .services import VirtualLabDockerImageService
import docker
from docker.errors import DockerException, NotFound
from django.http import JsonResponse, FileResponse
from django.utils import timezone
import mimetypes
from django.views.decorators.clickjacking import xframe_options_sameorigin

def is_student(user):
    """
    Check whether the logged-in user is a student.
    """

    return (
        user.is_authenticated
        and getattr(user, "is_student", False)
    )


def is_lab_manager(user):
    """
    Check whether the user can manage Virtual Lab operations.
    """

    return (
        user.is_authenticated
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_lecturer", False)
        )
    )




@login_required
def lab_catalog(request):
    """
    Display all active Virtual Labs created
    through the new Virtual Lab system.
    """

    labs = (
        VirtualLab.objects
        .filter(status="ACTIVE")
        .order_by("name")
    )

    lab_data = []

    for lab in labs:

        status = None

        if is_student(request.user):

            status = (
                VirtualLabAccessService
                .get_student_request_status(
                    request.user,
                    lab,
                )
            )

        lab_data.append({
            "lab": lab,
            "status": status,
        })

    return render(
        request,
        "virtuallab/lab_catalog.html",
        {
            "labs": lab_data,
        },
    )



@login_required
def lab_management(request):
    """
    Virtual Lab Management Center for administrators and lecturers.
    """

    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to manage Virtual Labs."
        )
        return redirect("virtuallab:lab_catalog")

    labs = (
        VirtualLab.objects
        .annotate(
            student_count=Count(
                "access_requests__student",
                filter=Q(access_requests__status="APPROVED"),
                distinct=True,
            ),
            pending_count=Count(
                "access_requests",
                filter=Q(access_requests__status="PENDING"),
                distinct=True,
            ),
            running_environment_count=Count(
                "student_environments",
                filter=Q(student_environments__status="RUNNING"),
                distinct=True,
            ),
            environment_count=Count(
                "student_environments",
                filter=~Q(student_environments__status="DELETED"),
                distinct=True,
            ),
        )
        .order_by("name")
    )

    total_labs = VirtualLab.objects.count()

    active_labs = VirtualLab.objects.filter(
        status="ACTIVE"
    ).count()

    inactive_labs = VirtualLab.objects.exclude(
        status="ACTIVE"
    ).count()

    total_students = (
        VirtualLabAccessRequest.objects
        .filter(status="APPROVED")
        .values("student")
        .distinct()
        .count()
    )

    running_environments = (
        StudentLabEnvironment.objects
        .filter(status="RUNNING")
        .count()
    )

    context = {
        "labs": labs,
        "total_labs": total_labs,
        "active_labs": active_labs,
        "inactive_labs": inactive_labs,
        "total_students": total_students,
        "running_environments": running_environments,
    }

    return render(
        request,
        "virtuallab/lab_management.html",
        context,
    )


@login_required
def toggle_lab_status(request, lab_id):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to change Virtual Lab status."
        )
        return redirect("virtuallab:lab_catalog")

    if request.method != "POST":
        return redirect("virtuallab:lab_management")

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
    )

    if lab.status == "ACTIVE":
        lab.status = "INACTIVE"
        action = "deactivated"
    else:
        lab.status = "ACTIVE"
        action = "activated"

    lab.save(update_fields=["status"])

    messages.success(
        request,
        f"Virtual Lab '{lab.name}' {action} successfully."
    )

    return redirect("virtuallab:lab_management")



@login_required
def create_lab(request):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to create Virtual Labs."
        )
        return redirect("virtuallab:lab_catalog")

    environments = (
        VirtualLabDockerEnvironment.objects
        .filter(status="READY")
        .order_by("environment_type", "name")
    )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        lab_type = request.POST.get("lab_type", "").strip()
        technology = request.POST.get("technology", "").strip()
        docker_environment_id = request.POST.get(
            "docker_environment"
        )
        allocated_ram = request.POST.get("allocated_ram", "").strip()
        allocated_storage = request.POST.get(
            "allocated_storage",
            ""
        ).strip()
        status = request.POST.get("status", "ACTIVE").strip()

        if not name:
            messages.error(request, "Lab name is required.")
            return render(
                request,
                "virtuallab/create_lab.html",
                {"environments": environments},
            )

        if not description:
            messages.error(request, "Lab description is required.")
            return render(
                request,
                "virtuallab/create_lab.html",
                {"environments": environments},
            )

        docker_environment = None

        if docker_environment_id:
            docker_environment = get_object_or_404(
                VirtualLabDockerEnvironment,
                id=docker_environment_id,
                status="READY",
            )

        try:
            allocated_ram = int(allocated_ram or 512)
        except ValueError:
            allocated_ram = 512

        try:
            allocated_storage = int(
                allocated_storage or 10240
            )
        except ValueError:
            allocated_storage = 10240

        valid_lab_types = {
            choice[0]
            for choice in VirtualLab.LAB_TYPE_CHOICES
        }

        if lab_type not in valid_lab_types:
            lab_type = "PROGRAMMING"

        valid_statuses = {
            choice[0]
            for choice in VirtualLab._meta.get_field(
                "status"
            ).choices
        }

        if status not in valid_statuses:
            status = "ACTIVE"

        VirtualLab.objects.create(
            name=name,
            description=description,
            lab_type=lab_type,
            technology=technology,
            docker_environment=docker_environment,
            allocated_ram=allocated_ram,
            allocated_storage=allocated_storage,
            status=status,
            created_by=request.user,
        )

        messages.success(
            request,
            f"Virtual Lab '{name}' created successfully."
        )

        return redirect("virtuallab:lab_management")

    return render(
        request,
        "virtuallab/create_lab.html",
        {
            "environments": environments,
            "lab_type_choices": VirtualLab.LAB_TYPE_CHOICES,
        },
    )


@login_required
def edit_lab(request, lab_id):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to edit Virtual Labs."
        )
        return redirect("virtuallab:lab_catalog")

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
    )

    environments = (
        VirtualLabDockerEnvironment.objects
        .filter(status="READY")
        .order_by("environment_type", "name")
    )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        lab_type = request.POST.get("lab_type", "").strip()
        technology = request.POST.get("technology", "").strip()
        docker_environment_id = request.POST.get(
            "docker_environment"
        )
        allocated_ram = request.POST.get(
            "allocated_ram",
            ""
        ).strip()
        allocated_storage = request.POST.get(
            "allocated_storage",
            ""
        ).strip()
        status = request.POST.get(
            "status",
            "ACTIVE"
        ).strip()

        if not name:
            messages.error(
                request,
                "Lab name is required."
            )
        elif not description:
            messages.error(
                request,
                "Lab description is required."
            )
        else:
            docker_environment = None

            if docker_environment_id:
                docker_environment = get_object_or_404(
                    VirtualLabDockerEnvironment,
                    id=docker_environment_id,
                    status="READY",
                )

            try:
                allocated_ram = int(
                    allocated_ram or 512
                )
            except ValueError:
                allocated_ram = 512

            try:
                allocated_storage = int(
                    allocated_storage or 10240
                )
            except ValueError:
                allocated_storage = 10240

            valid_lab_types = {
                choice[0]
                for choice in VirtualLab.LAB_TYPE_CHOICES
            }

            if lab_type not in valid_lab_types:
                lab_type = "PROGRAMMING"

            valid_statuses = {
                choice[0]
                for choice in VirtualLab._meta.get_field(
                    "status"
                ).choices
            }

            if status not in valid_statuses:
                status = "ACTIVE"

            lab.name = name
            lab.description = description
            lab.lab_type = lab_type
            lab.technology = technology
            lab.docker_environment = docker_environment
            lab.allocated_ram = allocated_ram
            lab.allocated_storage = allocated_storage
            lab.status = status

            lab.save()

            messages.success(
                request,
                f"Virtual Lab '{lab.name}' updated successfully."
            )

            return redirect(
                "virtuallab:lab_manager_overview",
                lab_id=lab.id,
            )

    return render(
        request,
        "virtuallab/edit_lab.html",
        {
            "lab": lab,
            "environments": environments,
            "lab_type_choices": VirtualLab.LAB_TYPE_CHOICES,
        },
    )


@login_required
def request_lab_access(request, lab_id):
    """
    Allow a student to request access to an active Virtual Lab.
    """

    if not is_student(request.user):

        messages.error(
            request,
            "Only students can request Virtual Lab access.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    if request.method != "POST":

        return redirect(
            "virtuallab:lab_catalog"
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    try:

        VirtualLabAccessService.create_request(
            student=request.user,
            lab=lab,
        )

        messages.success(
            request,
            f"Access request submitted for {lab.name}.",
        )

    except ValueError as exc:

        messages.warning(
            request,
            str(exc),
        )

    return redirect(
        "virtuallab:lab_catalog"
    )


@login_required
def my_lab_requests(request):
    """
    Display the student's Virtual Lab access requests.
    """

    if not is_student(request.user):

        messages.error(
            request,
            "This page is available only to students.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    requests = (
        VirtualLabAccessRequest.objects
        .filter(
            student=request.user
        )
        .select_related(
            "lab",
            "reviewed_by",
        )
        .order_by(
            "-requested_at"
        )
    )

    return render(
        request,
        "virtuallab/my_requests.html",
        {
            "requests": requests,
        },
    )

@login_required
def access_requests(request):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to manage Virtual Lab access."
        )
        return redirect("virtuallab:lab_catalog")

    # ---------------------------------------------------------
    # PENDING ACCESS REQUEST QUEUE
    # ---------------------------------------------------------

    previous_rejection_queryset = (
        VirtualLabAccessRequest.objects
        .filter(
            student=OuterRef("student"),
            lab=OuterRef("lab"),
            status="REJECTED",
        )
        .filter(
            Q(
                requested_at__lt=OuterRef("requested_at")
            )
            |
            Q(
                requested_at=OuterRef("requested_at"),
                pk__lt=OuterRef("pk"),
            )
        )
        .order_by(
            "-requested_at",
            "-pk",
        )
    )

    requests = (
        VirtualLabAccessRequest.objects
        .filter(status="PENDING")
        .select_related("student", "lab")
        .annotate(
            has_previous_rejection=Exists(
                previous_rejection_queryset
            ),
            previous_rejection_id=Subquery(
                previous_rejection_queryset.values("id")[:1]
            ),
            previous_rejection_reason=Subquery(
                previous_rejection_queryset.values("review_reason")[:1]
            ),
            previous_rejection_requested_at=Subquery(
                previous_rejection_queryset.values("requested_at")[:1]
            ),
            previous_rejection_reviewed_at=Subquery(
                previous_rejection_queryset.values("reviewed_at")[:1]
            ),
            previous_rejection_reviewer=Subquery(
                previous_rejection_queryset.values(
                    "reviewed_by__username"
                )[:1]
            ),
        )
        .order_by("-requested_at", "-pk")
    )

    # ---------------------------------------------------------
    # GLOBAL ACCESS STATISTICS
    # ---------------------------------------------------------

    total_labs = VirtualLab.objects.count()

    total_requests = VirtualLabAccessRequest.objects.count()

    pending_count = VirtualLabAccessRequest.objects.filter(
        status="PENDING"
    ).count()

    approved_count = VirtualLabAccessRequest.objects.filter(
        status="APPROVED"
    ).count()

    rejected_count = VirtualLabAccessRequest.objects.filter(
        status="REJECTED"
    ).count()

    cancelled_count = VirtualLabAccessRequest.objects.filter(
        status="CANCELLED"
    ).count()

    # ---------------------------------------------------------
    # ENVIRONMENT STATISTICS
    # ---------------------------------------------------------

    total_environments = (
        StudentLabEnvironment.objects
        .exclude(status="DELETED")
        .count()
    )

    provisioning_environment_count = (
        StudentLabEnvironment.objects
        .filter(status="PROVISIONING")
        .count()
    )

    ready_environment_count = (
        StudentLabEnvironment.objects
        .filter(status="READY")
        .count()
    )

    running_environment_count = (
        StudentLabEnvironment.objects
        .filter(status="RUNNING")
        .count()
    )

    stopped_environment_count = (
        StudentLabEnvironment.objects
        .filter(status="STOPPED")
        .count()
    )

    error_environment_count = (
        StudentLabEnvironment.objects
        .filter(status="ERROR")
        .count()
    )

    # ---------------------------------------------------------
    # LAB-WISE ACCESS STATISTICS
    # ---------------------------------------------------------

    labs = (
        VirtualLab.objects
        .annotate(
            total_requests=Count(
                "access_requests",
                distinct=True,
            ),
            pending_requests=Count(
                "access_requests",
                filter=Q(access_requests__status="PENDING"),
                distinct=True,
            ),
            approved_requests=Count(
                "access_requests",
                filter=Q(access_requests__status="APPROVED"),
                distinct=True,
            ),
            rejected_requests=Count(
                "access_requests",
                filter=Q(access_requests__status="REJECTED"),
                distinct=True,
            ),
            cancelled_requests=Count(
                "access_requests",
                filter=Q(access_requests__status="CANCELLED"),
                distinct=True,
            ),
            total_environments=Count(
                "student_environments",
                filter=~Q(student_environments__status="DELETED"),
                distinct=True,
            ),
            running_environments=Count(
                "student_environments",
                filter=Q(student_environments__status="RUNNING"),
                distinct=True,
            ),
        )
        .order_by("name")
    )

    return render(
        request,
        "virtuallab/access_requests.html",
        {
            # Existing data
            "requests": requests,
            "environments": (
                StudentLabEnvironment.objects
                .select_related("student", "lab")
                .exclude(status="DELETED")
                .order_by("-updated_at")
            ),

            # Global access statistics
            "total_labs": total_labs,
            "total_requests": total_requests,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "cancelled_count": cancelled_count,

            # Global environment statistics
            "total_environments": total_environments,
            "provisioning_environment_count": provisioning_environment_count,
            "ready_environment_count": ready_environment_count,
            "running_environment_count": running_environment_count,
            "stopped_environment_count": stopped_environment_count,
            "error_environment_count": error_environment_count,

            # Lab-wise statistics
            "labs": labs,
        },
    )

@login_required
def approve_access_request(request, request_id):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to approve access requests."
        )
        return redirect("virtuallab:access_requests")

    if request.method != "POST":
        return redirect("virtuallab:access_requests")

    access_request = get_object_or_404(
        VirtualLabAccessRequest,
        id=request_id,
    )

    return_to_detail = request.POST.get("return_to_detail") == "1"

    try:
        VirtualLabAccessService.approve_request(
            access_request=access_request,
            reviewer=request.user,
        )

        student_name = (
            access_request.student.get_full_name
            or access_request.student.username
        )

        messages.success(
            request,
            f"Access approved for {student_name} "
            f"for {access_request.lab.name}.",
        )

    except ValueError as exc:
        messages.error(request, str(exc))

    if return_to_detail:
        return redirect(
            "virtuallab:lab_access_details",
            lab_id=access_request.lab_id,
        )

    return redirect("virtuallab:access_requests")

@login_required
def reject_access_request(request, request_id):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to reject access requests."
        )
        return redirect("virtuallab:access_requests")

    if request.method != "POST":
        return redirect("virtuallab:access_requests")

    access_request = get_object_or_404(
        VirtualLabAccessRequest,
        id=request_id,
    )

    reason = request.POST.get("reason", "").strip()

    return_to_detail = request.POST.get("return_to_detail") == "1"

    try:
        VirtualLabAccessService.reject_request(
            access_request=access_request,
            reviewer=request.user,
            reason=reason,
        )

        messages.success(
            request,
            f"Access request for {access_request.lab.name} "
            f"was rejected.",
        )

    except ValueError as exc:
        messages.error(request, str(exc))

    if return_to_detail:
        return redirect(
            "virtuallab:lab_access_details",
            lab_id=access_request.lab_id,
        )

    return redirect("virtuallab:access_requests")
@login_required
def lab_access_details(request, lab_id):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to view Virtual Lab access details."
        )
        return redirect("virtuallab:lab_catalog")

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
    )

    # ---------------------------------------------------------
    # PREVIOUS REJECTION LOOKUP
    #
    # For every request, find the most recent REJECTED request
    # by the same student for the same laboratory that happened
    # before the current request.
    # ---------------------------------------------------------

    previous_rejection_queryset = (
        VirtualLabAccessRequest.objects
        .filter(
            student=OuterRef("student"),
            lab=OuterRef("lab"),
            status="REJECTED",
        )
        .filter(
            Q(
                requested_at__lt=OuterRef("requested_at")
            )
            |
            Q(
                requested_at=OuterRef("requested_at"),
                pk__lt=OuterRef("pk"),
            )
        )
        .order_by(
            "-requested_at",
            "-pk",
        )
    )

    # ---------------------------------------------------------
    # BASE ACCESS REQUEST QUERYSET
    # ---------------------------------------------------------

    all_access_requests = (
        VirtualLabAccessRequest.objects
        .filter(lab=lab)
        .select_related("student", "reviewed_by")
        .annotate(
            has_previous_rejection=Exists(
                previous_rejection_queryset
            ),

            previous_rejection_id=Subquery(
                previous_rejection_queryset
                .values("id")[:1]
            ),

            previous_rejection_reason=Subquery(
                previous_rejection_queryset
                .values("review_reason")[:1]
            ),

            previous_rejection_requested_at=Subquery(
                previous_rejection_queryset
                .values("requested_at")[:1]
            ),

            previous_rejection_reviewed_at=Subquery(
                previous_rejection_queryset
                .values("reviewed_at")[:1]
            ),

            previous_rejection_reviewer=Subquery(
                previous_rejection_queryset
                .values("reviewed_by__username")[:1]
            ),
        )
        .order_by("-requested_at", "-pk")
    )

    # ---------------------------------------------------------
    # FILTER INPUTS
    # ---------------------------------------------------------

    selected_status = request.GET.get("status", "").strip().upper()
    student_search = request.GET.get("search", "").strip()

    valid_statuses = {
        "PENDING",
        "APPROVED",
        "REJECTED",
        "CANCELLED",
    }

    if selected_status not in valid_statuses:
        selected_status = ""

    # ---------------------------------------------------------
    # FILTERED ACCESS REQUESTS
    #
    # Important:
    # Filtering happens AFTER previous-rejection information
    # has been calculated.
    # ---------------------------------------------------------

    access_requests = all_access_requests

    if selected_status:
        access_requests = access_requests.filter(
            status=selected_status
        )

    if student_search:
        access_requests = access_requests.filter(
            Q(student__username__icontains=student_search)
            |
            Q(student__first_name__icontains=student_search)
            |
            Q(student__last_name__icontains=student_search)
        )

    # ---------------------------------------------------------
    # ENVIRONMENTS
    # ---------------------------------------------------------

    environment_queryset = (
        StudentLabEnvironment.objects
        .filter(lab=lab)
        .select_related("student")
        .exclude(status="DELETED")
        .order_by("-updated_at")
    )

    # ---------------------------------------------------------
    # GLOBAL LAB STATISTICS
    #
    # These remain based on ALL requests, not filtered requests.
    # ---------------------------------------------------------

    total_requests = all_access_requests.count()

    pending_count = all_access_requests.filter(
        status="PENDING"
    ).count()

    approved_count = all_access_requests.filter(
        status="APPROVED"
    ).count()

    rejected_count = all_access_requests.filter(
        status="REJECTED"
    ).count()

    cancelled_count = all_access_requests.filter(
        status="CANCELLED"
    ).count()

    # ---------------------------------------------------------
    # ENVIRONMENT STATISTICS
    # ---------------------------------------------------------

    total_environments = environment_queryset.count()

    running_environments = environment_queryset.filter(
        status="RUNNING"
    ).count()

    ready_environments = environment_queryset.filter(
        status="READY"
    ).count()

    provisioning_environments = environment_queryset.filter(
        status="PROVISIONING"
    ).count()

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------

    context = {
        "lab": lab,

        # Filtered request table
        "access_requests": access_requests,

        # Environment data
        "environments": environment_queryset,

        # Global request statistics
        "total_requests": total_requests,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "cancelled_count": cancelled_count,

        # Environment statistics
        "total_environments": total_environments,
        "running_environments": running_environments,
        "ready_environments": ready_environments,
        "provisioning_environments": provisioning_environments,

        # Current filters
        "selected_status": selected_status,
        "student_search": student_search,

        # Filtered result count
        "filtered_request_count": access_requests.count(),
    }

    return render(
        request,
        "virtuallab/lab_access_details.html",
        context,
    )

@login_required
def lab_overview(request, lab_id):
    """
    Display the selected Virtual Lab information before
    the student enters the actual lab environment.
    """

    if not is_student(request.user):
        messages.error(
            request,
            "This page is available only to students.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    access_request = (
        VirtualLabAccessRequest.objects
        .filter(
            student=request.user,
            lab=lab,
        )
        .order_by("-requested_at")
        .first()
    )

    environment = (
        StudentLabEnvironment.objects
        .filter(
            student=request.user,
            lab=lab,
        )
        .exclude(status="DELETED")
        .first()
    )

    return render(
        request,
        "virtuallab/lab_overview.html",
        {
            "lab": lab,
            "access_request": access_request,
            "environment": environment,
        },
    )



@login_required
def toggle_student_lab_access(request, request_id):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to change student lab access."
        )
        return redirect("virtuallab:lab_catalog")

    if request.method != "POST":
        return redirect("virtuallab:access_requests")

    access_request = get_object_or_404(
        VirtualLabAccessRequest,
        id=request_id,
        status="APPROVED",
    )

    if access_request.is_active:
        access_request.is_active = False
        action = "deactivated"
    else:
        access_request.is_active = True
        action = "activated"

    access_request.save(update_fields=["is_active"])

    student_name = (
        str(access_request.student.get_full_name or "").strip()
        or str(access_request.student.username)
    )

    messages.success(
        request,
        f"Access for {student_name} in "
        f"{access_request.lab.name} was {action} successfully."
    )

    return redirect(
        "virtuallab:lab_access_details",
        lab_id=access_request.lab_id,
    )




@login_required
def access_lab(request, lab_id):
    """
    Enter the actual Virtual Lab after access has been approved
    and the student's Docker environment is ready.
    """

    if not is_student(request.user):
        messages.error(
            request,
            "This page is available only to students.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    if request.method != "POST":
        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab_id,
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    access_request = (
        VirtualLabAccessRequest.objects
        .filter(
            student=request.user,
            lab=lab,
            status="APPROVED",
            is_active=True,
        )
        .first()
    )

    if not access_request:
        messages.warning(
            request,
            "Your access to this Virtual Lab is currently unavailable. "
            "Please contact your lecturer or administrator for assistance."
        )
        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    environment = (
        StudentLabEnvironment.objects
        .filter(
            student=request.user,
            lab=lab,
        )
        .exclude(status="DELETED")
        .first()
    )

    if not environment:
        messages.error(
            request,
            "Your Virtual Lab environment has not been provisioned yet.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab_id,
        )

    if environment.status not in {
        "READY",
        "RUNNING",
    }:
        messages.warning(
            request,
            f"Your lab environment is currently "
            f"{environment.get_status_display()}.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab_id,
        )

    client_ip = request.META.get(
        "REMOTE_ADDR"
    )

    try:

        session = VirtualLabSessionService.open_session(
            student=request.user,
            lab=lab,
            client_ip=client_ip,
        )

    except ValueError as exc:

        messages.error(
            request,
            str(exc),
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab_id,
        )

    return redirect(
        "virtuallab:lab_session",
        lab_id=lab.id,
    )



@login_required
def create_workspace_file(request, lab_id):
    """
    Create an empty file inside the student's Virtual Lab workspace.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required.",
            },
            status=405,
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment is not ready.",
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid JSON request.",
            },
            status=400,
        )

    name = str(data.get("name", "")).strip()
    parent_path = (
        str(data.get("path", ""))
        .strip()
        .replace("\\", "/")
        .strip("/")
    )

    if not name:
        return JsonResponse(
            {
                "success": False,
                "error": "File name is required.",
            },
            status=400,
        )

    # A file name must be a single name, not a path.
    if name in {".", ".."} or "/" in name or "\\" in name:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid file name.",
            },
            status=400,
        )

    root = Path(environment.workspace_path).resolve()
    parent = (root / parent_path).resolve()

    try:
        parent.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid workspace path.",
            },
            status=400,
        )

    if not parent.exists() or not parent.is_dir():
        return JsonResponse(
            {
                "success": False,
                "error": "Parent folder does not exist.",
            },
            status=400,
        )

    file_path = (parent / name).resolve()

    try:
        file_path.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid file path.",
            },
            status=400,
        )

    if file_path.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "A file or folder with this name already exists.",
            },
            status=409,
        )

    try:
        file_path.touch()
        session.last_activity = timezone.now()
        session.save(update_fields=["last_activity"])

    except OSError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    relative_file = file_path.relative_to(root)

    return JsonResponse(
        {
            "success": True,
            "message": "File created successfully.",
            "name": name,
            "path": str(relative_file).replace("\\", "/"),
        }
    )


@login_required
def create_workspace_folder(request, lab_id):
    """
    Create a folder inside the student's Virtual Lab workspace.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required.",
            },
            status=405,
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment is not ready.",
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid JSON request.",
            },
            status=400,
        )

    name = str(data.get("name", "")).strip()
    parent_path = (
        str(data.get("path", ""))
        .strip()
        .replace("\\", "/")
        .strip("/")
    )

    if not name:
        return JsonResponse(
            {
                "success": False,
                "error": "Folder name is required.",
            },
            status=400,
        )

    if name in {".", ".."} or "/" in name or "\\" in name:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid folder name.",
            },
            status=400,
        )

    root = Path(environment.workspace_path).resolve()
    parent = (root / parent_path).resolve()

    try:
        parent.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid workspace path.",
            },
            status=400,
        )

    if not parent.exists() or not parent.is_dir():
        return JsonResponse(
            {
                "success": False,
                "error": "Parent folder does not exist.",
            },
            status=400,
        )

    folder_path = (parent / name).resolve()

    try:
        folder_path.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid folder path.",
            },
            status=400,
        )

    if folder_path.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "A file or folder with this name already exists.",
            },
            status=409,
        )

    try:
        folder_path.mkdir()
        session.last_activity = timezone.now()
        session.save(update_fields=["last_activity"])

    except OSError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    relative_folder = folder_path.relative_to(root)

    return JsonResponse(
        {
            "success": True,
            "message": "Folder created successfully.",
            "name": name,
            "path": str(relative_folder).replace("\\", "/"),
        }
    )


@login_required
def delete_workspace_item(request, lab_id):
    """
    Delete a file or folder from the student's Virtual Lab workspace.
    Folders are deleted recursively after explicit confirmation from the UI.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required.",
            },
            status=405,
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment is not ready.",
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid JSON request.",
            },
            status=400,
        )

    item_path = (
        str(data.get("path", ""))
        .strip()
        .replace("\\", "/")
        .strip("/")
    )

    if not item_path:
        return JsonResponse(
            {
                "success": False,
                "error": "File or folder path is required.",
            },
            status=400,
        )

    root = Path(environment.workspace_path).resolve()
    target = (root / item_path).resolve()

    # Never allow deletion outside /workspace.
    try:
        target.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid workspace path.",
            },
            status=400,
        )

    # Never allow deletion of the workspace itself.
    if target == root:
        return JsonResponse(
            {
                "success": False,
                "error": "The workspace root cannot be deleted.",
            },
            status=400,
        )

    if not target.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "File or folder does not exist.",
            },
            status=404,
        )

    item_name = target.name
    item_type = "folder" if target.is_dir() else "file"
    relative_path = target.relative_to(root)

    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

        session.last_activity = timezone.now()
        session.save(update_fields=["last_activity"])

    except OSError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "message": f"{item_type.capitalize()} deleted successfully.",
            "name": item_name,
            "path": str(relative_path).replace("\\", "/"),
            "type": item_type,
        }
    )


@login_required
def upload_workspace_file(request, lab_id):
    """
    Upload a single file into the student's Virtual Lab workspace.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment is not ready.",
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return JsonResponse(
            {
                "success": False,
                "error": "No file was selected.",
            },
            status=400,
        )

    # Current folder inside /workspace
    relative_path = (
        request.POST.get("path", "")
        .strip()
        .replace("\\", "/")
        .strip("/")
    )

    root = Path(
        environment.workspace_path
    ).resolve()

    parent = (
        root / relative_path
    ).resolve()

    # Security: parent must remain inside student's workspace.
    try:
        parent.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid workspace path.",
            },
            status=400,
        )

    if not parent.exists() or not parent.is_dir():
        return JsonResponse(
            {
                "success": False,
                "error": "Destination folder does not exist.",
            },
            status=400,
        )

    # Keep only the filename.
    filename = Path(
        uploaded_file.name
    ).name.strip()

    if not filename or filename in {".", ".."}:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid file name.",
            },
            status=400,
        )

    destination = (
        parent / filename
    ).resolve()

    # Security: destination must remain inside workspace.
    try:
        destination.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid destination path.",
            },
            status=400,
        )

    if destination.exists():
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "A file or folder with this name "
                    "already exists."
                ),
            },
            status=409,
        )

    try:

        with destination.open("wb+") as destination_file:

            for chunk in uploaded_file.chunks():
                destination_file.write(chunk)

        session.last_activity = timezone.now()
        session.save(
            update_fields=["last_activity"]
        )

    except OSError as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    relative_file = (
        destination
        .relative_to(root)
    )

    return JsonResponse(
        {
            "success": True,
            "message": "File uploaded successfully.",
            "name": filename,
            "path": str(
                relative_file
            ).replace("\\", "/"),
        }
    )


@login_required
def workspace_files(request, lab_id):

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Virtual lab environment is not ready."
                ),
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    root = Path(
        environment.workspace_path
    ).resolve()

    relative_path = (
        request.GET.get("path", "")
        .strip()
        .replace("\\", "/")
    )

    current_path = (
        root / relative_path
    ).resolve()

    # Prevent path traversal outside the student's workspace.
    try:

        current_path.relative_to(root)

    except ValueError:

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid workspace path.",
            },
            status=400,
        )

    if not current_path.exists():

        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path does not exist.",
            },
            status=404,
        )

    if not current_path.is_dir():

        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not a directory.",
            },
            status=400,
        )

    entries = []

    try:

        children = sorted(
            current_path.iterdir(),
            key=lambda item: (
                not item.is_dir(),
                item.name.lower(),
            ),
        )

        for item in children:

            try:

                relative_item = (
                    item.resolve().relative_to(root)
                )

            except ValueError:

                # Ignore symlinks that point outside the workspace.
                continue

            stat = item.stat()

            entries.append(
                {
                    "name": item.name,
                    "type": (
                        "directory"
                        if item.is_dir()
                        else "file"
                    ),
                    "path": str(
                        relative_item
                    ).replace("\\", "/"),
                    "size": (
                        stat.st_size
                        if item.is_file()
                        else None
                    ),
                }
            )

    except OSError as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "current_path": relative_path,
            "entries": entries,
        }
    )


@login_required
def workspace_file(request, lab_id):

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment is not ready.",
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    relative_path = (
        request.GET.get("path", "")
        .strip()
        .replace("\\", "/")
    )

    if not relative_path:
        return JsonResponse(
            {
                "success": False,
                "error": "File path is required.",
            },
            status=400,
        )

    root = Path(
        environment.workspace_path
    ).resolve()

    file_path = (
        root / relative_path
    ).resolve()

    # Security: prevent ../ traversal.
    try:

        file_path.relative_to(root)

    except ValueError:

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid file path.",
            },
            status=400,
        )

    if not file_path.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "File was not found.",
            },
            status=404,
        )

    if not file_path.is_file():
        return JsonResponse(
            {
                "success": False,
                "error": "Requested path is not a file.",
            },
            status=400,
        )

    # Keep the first editor version intentionally text-focused.
    allowed_extensions = {
        ".py", ".txt", ".md", ".json", ".csv", ".xml",
        ".html", ".css", ".js", ".java", ".c", ".cpp",
        ".h", ".hpp", ".sh", ".yaml", ".yml", ".sql",
    }

    file_extension = file_path.suffix.lower()

    print("========== SAVE DEBUG ==========")
    print("FILE PATH:", file_path)
    print("SUFFIX:", file_path.suffix)
    print("EXTENSION:", file_extension)
    print("ALLOWED:", file_extension in allowed_extensions)
    print("================================")

    # Files without an extension are editable text files.
    if file_extension and file_extension not in allowed_extensions:

        return JsonResponse(
            {
                "success": False,
                "error": "This file type cannot be edited.",
            },
            status=415,
        )

    print("PASSED EXTENSION CHECK")
    # Prevent accidentally loading extremely large files.
    max_file_size = 1024 * 1024

    if file_path.stat().st_size > max_file_size:
        return JsonResponse(
            {
                "success": False,
                "error": "File is too large to open in the editor.",
            },
            status=413,
        )

    try:

        content = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    except OSError as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "name": file_path.name,
            "path": relative_path,
            "content": content,
        }
    )


@login_required
@xframe_options_sameorigin
def workspace_file_content(request, lab_id):
    """
    Safely serve a student's workspace file for browser preview/download.
    Used for PDFs, images, audio, video, documents, spreadsheets, etc.
    """

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment is not ready.",
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    relative_path = (
        request.GET.get("path", "")
        .strip()
        .replace("\\", "/")
        .strip("/")
    )

    if not relative_path:
        return JsonResponse(
            {
                "success": False,
                "error": "File path is required.",
            },
            status=400,
        )

    root = Path(
        environment.workspace_path
    ).resolve()

    file_path = (
        root / relative_path
    ).resolve()

    # Security: never allow access outside this student's workspace.
    try:
        file_path.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid workspace path.",
            },
            status=400,
        )

    if not file_path.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "File was not found.",
            },
            status=404,
        )

    if not file_path.is_file():
        return JsonResponse(
            {
                "success": False,
                "error": "Requested path is not a file.",
            },
            status=400,
        )

    # Determine browser MIME type.
    content_type, encoding = mimetypes.guess_type(
        file_path.name
    )

    if not content_type:
        content_type = "application/octet-stream"

    try:
        response = FileResponse(
            open(file_path, "rb"),
            content_type=content_type,
        )

        response["Content-Disposition"] = (
            f'inline; filename="{file_path.name}"'
        )

        return response

    except OSError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )



@login_required
def rename_workspace_item(request, lab_id):
    """
    Rename a file or folder inside the student's Virtual Lab workspace.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required.",
            },
            status=405,
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": "No active virtual lab session was found.",
            },
            status=403,
        )

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment was not found.",
            },
            status=404,
        )

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse(
            {
                "success": False,
                "error": "Virtual lab environment is not ready.",
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Workspace path is not configured.",
            },
            status=500,
        )

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid JSON request.",
            },
            status=400,
        )

    old_path = (
        str(data.get("path", ""))
        .strip()
        .replace("\\", "/")
        .strip("/")
    )
    new_name = str(data.get("name", "")).strip()

    if not old_path:
        return JsonResponse(
            {
                "success": False,
                "error": "Item path is required.",
            },
            status=400,
        )

    if not new_name:
        return JsonResponse(
            {
                "success": False,
                "error": "New name is required.",
            },
            status=400,
        )

    if (
        new_name in {".", ".."}
        or "/" in new_name
        or "\\" in new_name
    ):
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid name.",
            },
            status=400,
        )

    root = Path(environment.workspace_path).resolve()
    source = (root / old_path).resolve()

    try:
        source.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid workspace path.",
            },
            status=400,
        )

    if source == root:
        return JsonResponse(
            {
                "success": False,
                "error": "The workspace root cannot be renamed.",
            },
            status=400,
        )

    if not source.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "File or folder was not found.",
            },
            status=404,
        )

    target = (source.parent / new_name).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid destination path.",
            },
            status=400,
        )

    if target.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "A file or folder with this name already exists.",
            },
            status=409,
        )

    try:
        source.rename(target)
        session.last_activity = timezone.now()
        session.save(update_fields=["last_activity"])
    except OSError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    relative_target = target.relative_to(root)

    return JsonResponse(
        {
            "success": True,
            "message": "Item renamed successfully.",
            "name": new_name,
            "path": str(relative_target).replace("\\", "/"),
        }
    )


@login_required
def save_workspace_file(request, lab_id):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Only POST requests are allowed.",
        }, status=405)

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse({
            "success": False,
            "error": "No active virtual lab session was found.",
        }, status=403)

    environment = session.environment

    if not environment:
        return JsonResponse({
            "success": False,
            "error": "Virtual lab environment was not found.",
        }, status=404)

    if environment.status not in {"READY", "RUNNING"}:
        return JsonResponse({
            "success": False,
            "error": "Virtual lab environment is not ready.",
        }, status=409)

    if not environment.workspace_path:
        return JsonResponse({
            "success": False,
            "error": "Workspace path is not configured.",
        }, status=500)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({
            "success": False,
            "error": "Invalid request payload.",
        }, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({
            "success": False,
            "error": "Invalid request payload.",
        }, status=400)

    relative_path = str(
        payload.get("path", "")
    ).strip().replace("\\", "/").strip("/")

    if not relative_path:
        return JsonResponse({
            "success": False,
            "error": "File path is required.",
        }, status=400)

    root = Path(environment.workspace_path).resolve()
    file_path = (root / relative_path).resolve()

    # Keep the file inside the assigned workspace.
    try:
        file_path.relative_to(root)
    except ValueError:
        return JsonResponse({
            "success": False,
            "error": "Invalid file path.",
        }, status=400)

    if not file_path.exists():
        return JsonResponse({
            "success": False,
            "error": "File does not exist.",
        }, status=404)

    if not file_path.is_file():
        return JsonResponse({
            "success": False,
            "error": "Requested path is not a file.",
        }, status=400)

    file_extension = file_path.suffix.lower()
    max_file_size = 10 * 1024 * 1024  # 10 MiB

    try:
        # Excel workbooks are binary, not text.
        if file_extension in {".xlsx", ".xls"}:
            excel_data = payload.get("excel_data")

            if not isinstance(excel_data, str) or not excel_data:
                return JsonResponse({
                    "success": False,
                    "error": "Excel workbook data is missing.",
                }, status=400)

            # Check encoded length before decoding.
            if len(excel_data) > ((max_file_size + 2) // 3) * 4 + 4:
                return JsonResponse({
                    "success": False,
                    "error": "Excel file is too large to save.",
                }, status=413)

            try:
                workbook_bytes = base64.b64decode(
                    excel_data,
                    validate=True,
                )
            except (ValueError, base64.binascii.Error):
                return JsonResponse({
                    "success": False,
                    "error": "Invalid Excel workbook data.",
                }, status=400)

            if not workbook_bytes:
                return JsonResponse({
                    "success": False,
                    "error": "Excel workbook data is empty.",
                }, status=400)

            if len(workbook_bytes) > max_file_size:
                return JsonResponse({
                    "success": False,
                    "error": "Excel file is too large to save.",
                }, status=413)

            # The frontend must serialize the workbook in the
            # correct format before sending it here.
            file_path.write_bytes(workbook_bytes)

        else:
            allowed_extensions = {
                ".py", ".txt", ".md", ".json", ".csv",
                ".xml", ".html", ".css", ".js", ".java",
                ".c", ".cpp", ".h", ".hpp", ".sh",
                ".yaml", ".yml", ".sql",
            }

            if file_extension and file_extension not in allowed_extensions:
                return JsonResponse({
                    "success": False,
                    "error": "This file type cannot be edited.",
                }, status=415)

            content = payload.get("content", "")

            if not isinstance(content, str):
                return JsonResponse({
                    "success": False,
                    "error": "File content must be text.",
                }, status=400)

            if len(content.encode("utf-8")) > 1024 * 1024:
                return JsonResponse({
                    "success": False,
                    "error": "File is too large to save.",
                }, status=413)

            file_path.write_text(
                content,
                encoding="utf-8",
            )

    except OSError as exc:
        return JsonResponse({
            "success": False,
            "error": str(exc),
        }, status=500)

    session.last_activity = timezone.now()
    session.save(update_fields=["last_activity"])

    return JsonResponse({
        "success": True,
        "name": file_path.name,
        "path": relative_path,
        "message": "File saved successfully.",
    })



@login_required
def run_code(request, lab_id):
    """
    Execute supported source files inside the student's
    existing Virtual Lab Docker container.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    # ---------------------------------------------------------
    # LAB
    # ---------------------------------------------------------

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    # ---------------------------------------------------------
    # ACTIVE SESSION
    # ---------------------------------------------------------

    session = (
        LabSession.objects
        .select_related(
            "lab",
            "environment",
        )
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "No active virtual lab session "
                    "was found."
                ),
            },
            status=403,
        )

    # ---------------------------------------------------------
    # ENVIRONMENT
    # ---------------------------------------------------------

    environment = session.environment

    if not environment:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Virtual lab environment "
                    "was not found."
                ),
            },
            status=404,
        )

    if environment.status not in {
        "READY",
        "RUNNING",
    }:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Virtual lab environment "
                    "is not ready."
                ),
            },
            status=409,
        )

    if not environment.container_id:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Docker container is not "
                    "available."
                ),
            },
            status=409,
        )

    if not environment.workspace_path:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Workspace path is not configured."
                ),
            },
            status=500,
        )

    # ---------------------------------------------------------
    # REQUEST DATA
    # ---------------------------------------------------------

    try:
        payload = json.loads(
            request.body.decode("utf-8")
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request payload.",
            },
            status=400,
        )

    relative_path = str(
        payload.get("path", "")
    ).strip().replace("\\", "/")

    content = payload.get(
        "content",
        "",
    )

    if not relative_path:
        return JsonResponse(
            {
                "success": False,
                "error": "File path is required.",
            },
            status=400,
        )

    if not isinstance(content, str):
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "File content must be text."
                ),
            },
            status=400,
        )

    # ---------------------------------------------------------
    # SUPPORTED FILE TYPES
    # ---------------------------------------------------------

    extension = Path(
        relative_path
    ).suffix.lower()

    supported_extensions = {
        ".py",
        ".java",
        ".c",
        ".cpp",
        ".cc",
        ".cxx",
        ".sh",
    }

    if extension not in supported_extensions:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "This file type cannot be "
                    "executed."
                ),
            },
            status=415,
        )

    # ---------------------------------------------------------
    # WORKSPACE SECURITY
    # ---------------------------------------------------------

    root = Path(
        environment.workspace_path
    ).resolve()

    file_path = (
        root / relative_path
    ).resolve()

    try:
        file_path.relative_to(root)

    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Invalid workspace path."
                ),
            },
            status=400,
        )

    if not file_path.exists():
        return JsonResponse(
            {
                "success": False,
                "error": "File was not found.",
            },
            status=404,
        )

    if not file_path.is_file():
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "The selected path is not a file."
                ),
            },
            status=400,
        )

    # ---------------------------------------------------------
    # SAVE CURRENT EDITOR CONTENT
    # ---------------------------------------------------------

    try:
        file_path.write_text(
            content,
            encoding="utf-8",
        )

    except OSError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Unable to save file before "
                    f"execution: {exc}"
                ),
            },
            status=500,
        )

    # ---------------------------------------------------------
    # DOCKER
    # ---------------------------------------------------------

    client = None

    try:
        client = docker.from_env()

        client.ping()

        container = client.containers.get(
            environment.container_id
        )

        container.reload()

        if container.status != "running":
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "The Virtual Lab Docker "
                        "container is not running."
                    ),
                },
                status=409,
            )

        # -----------------------------------------------------
        # CONTAINER PATH
        # -----------------------------------------------------

        container_file = (
            "/workspace/"
            + relative_path.lstrip("/")
        )

        # -----------------------------------------------------
        # EXECUTION COMMAND
        # -----------------------------------------------------

        if extension == ".py":

            command = [
                "python3",
                f"/workspace/{relative_path}",
            ]

        elif extension == ".java":

            class_name = Path(
                relative_path
            ).stem

            command = [
                "/bin/sh",
                "-c",
                (
                    f"javac {container_file} "
                    f"&& java -cp "
                    f"$(dirname {container_file}) "
                    f"{class_name}"
                ),
            ]

        
        elif extension == ".c":

            output_file = "/tmp/vlab_program"

            # MPI mode can be selected from the Run Code request.
            use_mpi = bool(payload.get("use_mpi", False))

            compiler = "mpicc" if use_mpi else "gcc"

            compile_command = [
                compiler,
                container_file,
                "-o",
                output_file,
            ]

            if use_mpi:
                command = [
                    "/bin/sh",
                    "-c",
                    (
                        f"{compiler} "
                        f"'{container_file}' "
                        f"-o '{output_file}' "
                        f"&& mpirun --allow-run-as-root "
                        f"-np 4 '{output_file}'"
                    ),
                ]
            else:
                command = [
                    "/bin/sh",
                    "-c",
                    (
                        f"gcc '{container_file}' "
                        f"-o '{output_file}' "
                        f"&& '{output_file}'"
                    ),
                ]


        elif extension in {
            ".cpp",
            ".cc",
            ".cxx",
        }:

            output_file = "/tmp/vlab_program"

            command = [
                "/bin/sh",
                "-c",
                (
                    f"g++ {container_file} "
                    f"-o {output_file} "
                    f"&& {output_file}"
                ),
            ]

        elif extension == ".sh":

            command = [
                "/bin/bash",
                container_file,
            ]

        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Unsupported executable "
                        "file type."
                    ),
                },
                status=415,
            )

        # -----------------------------------------------------
        # EXECUTE
        # -----------------------------------------------------

        result = container.exec_run(
            command,
            workdir="/workspace",
            stdout=True,
            stderr=True,
            demux=True,
        )

        exit_code = result.exit_code

        stdout = ""
        stderr = ""

        if result.output:
            output = result.output

            if isinstance(output, tuple):
                stdout_bytes, stderr_bytes = output

                if stdout_bytes:
                    stdout = stdout_bytes.decode(
                        "utf-8",
                        errors="replace",
                    )

                if stderr_bytes:
                    stderr = stderr_bytes.decode(
                        "utf-8",
                        errors="replace",
                    )

            elif isinstance(output, bytes):
                stdout = output.decode(
                    "utf-8",
                    errors="replace",
                )

            else:
                stdout = str(output)

        # -----------------------------------------------------
        # SESSION ACTIVITY
        # -----------------------------------------------------

        session.last_activity = timezone.now()

        session.save(
            update_fields=[
                "last_activity",
            ]
        )

        # -----------------------------------------------------
        # RESPONSE
        # -----------------------------------------------------

        return JsonResponse(
            {
                "success": True,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "output": (
                    stdout
                    + (
                        "\n"
                        if stdout and stderr
                        else ""
                    )
                    + stderr
                ),
                "file": relative_path,
            }
        )

    except NotFound:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "The Docker container "
                    "could not be found."
                ),
            },
            status=404,
        )

    except DockerException as exc:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Docker execution failed: "
                    f"{exc}"
                ),
            },
            status=500,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Code execution failed: "
                    f"{exc}"
                ),
            },
            status=500,
        )

    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass




@login_required
def terminal_command(request, lab_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:

        return JsonResponse(
            {
                "success": False,
                "error": (
                    "No active virtual lab "
                    "session was found."
                ),
            },
            status=403,
        )

    environment = session.environment

    if not environment:

        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Virtual lab environment "
                    "was not found."
                ),
            },
            status=404,
        )

    try:

        payload = json.loads(
            request.body.decode("utf-8")
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request payload.",
            },
            status=400,
        )

    command = str(
        payload.get("command", "")
    ).strip()

    try:

        result = (
            VirtualLabTerminalService
            .execute_command(
                environment=environment,
                command=command,
            )
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=400,
        )

    session.last_activity = timezone.now()

    session.save(
        update_fields=[
            "last_activity",
        ]
    )

    return JsonResponse(
        {
            "success": True,
            "result": result,
        }
    )

@login_required
def lab_session(request, lab_id):
    """
    Virtual Lab home page.

    This page is the entry point after the student
    successfully accesses a Virtual Lab.
    """

    if not is_student(request.user):
        messages.error(
            request,
            "This page is available only to students.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        messages.warning(
            request,
            "You do not have an active Virtual Lab session.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    environment = session.environment

    if not environment:
        messages.error(
            request,
            "Virtual Lab environment was not found.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    if environment.status not in {"READY", "RUNNING"}:
        messages.warning(
            request,
            "Your Virtual Lab environment is not ready.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    # ---------------------------------------------------------
    # ASSIGNMENTS LINKED TO THIS NEW VIRTUAL LAB
    # ---------------------------------------------------------
    assignment_placements = (
        AssessmentPlacement.objects
        .filter(
            virtual_lab=lab
        )
        .select_related("assessment")
        .order_by(
            "assessment__title"
        )
    )

    assignments = [
        placement.assessment
        for placement in assignment_placements
    ]

    return render(
        request,
        "virtuallab/lab_session.html",
        {
            "lab": lab,
            "session": session,
            "environment": environment,
            "assignments": assignments,
        },
    )

@login_required
def lab_assignments(request, lab_id):
    """
    Display assessments assigned specifically to this Virtual Lab.
    """

    if not is_student(request.user):
        messages.error(
            request,
            "This page is available only to students.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    # Student must have an active Virtual Lab session.
    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        messages.warning(
            request,
            "You do not have an active Virtual Lab session.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    environment = session.environment

    if not environment:
        messages.error(
            request,
            "Virtual Lab environment was not found.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    if environment.status not in {
        "READY",
        "RUNNING",
    }:
        messages.warning(
            request,
            "Your Virtual Lab environment is not ready.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    # ---------------------------------------------------------
    # GET ASSESSMENTS ASSIGNED TO THIS VIRTUAL LAB
    # ---------------------------------------------------------

    assignment_placements = (
        AssessmentPlacement.objects
        .filter(
            virtual_lab=lab
        )
        .select_related("assessment")
        .order_by(
            "assessment__title"
        )
    )

    assignments = [
        placement.assessment
        for placement in assignment_placements
    ]

    return render(
        request,
        "virtuallab/lab_assignments.html",
        {
            "lab": lab,
            "session": session,
            "environment": environment,
            "assignments": assignments,
        },
    )

@login_required
def terminal(request, lab_id):
    """
    Standalone Virtual Lab terminal page.
    """

    if not is_student(request.user):
        messages.error(
            request,
            "This page is available only to students.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        messages.warning(
            request,
            "You do not have an active Virtual Lab session.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    environment = session.environment

    if not environment:
        messages.error(
            request,
            "Virtual Lab environment was not found.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    if environment.status not in {"READY", "RUNNING"}:
        messages.warning(
            request,
            "Your Virtual Lab environment is not ready.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    return render(
        request,
        "virtuallab/terminal.html",
        {
            "lab": lab,
            "session": session,
            "environment": environment,
        },
    )





@login_required
def file_manager(request, lab_id):
    """
    Virtual Lab File Manager.

    Displays the student's workspace files and folders.
    """

    if not is_student(request.user):
        messages.error(
            request,
            "This page is available only to students.",
        )

        return redirect(
            "virtuallab:lab_catalog"
        )

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
        status="ACTIVE",
    )

    session = (
        LabSession.objects
        .select_related("environment")
        .filter(
            student=request.user,
            lab=lab,
            status="ACTIVE",
        )
        .first()
    )

    if not session:
        messages.warning(
            request,
            "You do not have an active Virtual Lab session.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    environment = session.environment

    if not environment:
        messages.error(
            request,
            "Virtual Lab environment was not found.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    if environment.status not in {"READY", "RUNNING"}:
        messages.warning(
            request,
            "Your Virtual Lab environment is not ready.",
        )

        return redirect(
            "virtuallab:lab_overview",
            lab_id=lab.id,
        )

    return render(
        request,
        "virtuallab/file_manager.html",
        {
            "lab": lab,
            "session": session,
            "environment": environment,
        },
    )
@login_required
def lab_resources(request, lab_id):
    """
    Display available resources for students in a Virtual Lab.
    """

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
    )

    resources = (
        LabResource.objects
        .filter(
            lab=lab,
            is_active=True,
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "virtuallab/lab_resources.html",
        {
            "lab": lab,
            "resources": resources,
        },
    )

@login_required
def manage_lab_resources(request, lab_id):
    """
    Display resources for a Virtual Lab to authorized lab managers.
    """

    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to manage Virtual Lab resources."
        )
        return redirect("virtuallab:lab_catalog")

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
    )

    resources = (
        LabResource.objects
        .filter(lab=lab)
        .select_related("uploaded_by")
        .order_by("-created_at")
    )

    active_resource_count = resources.filter(
        is_active=True
    ).count()

    resource_type_count = (
        resources
        .values("resource_type")
        .distinct()
        .count()
    )

    return render(
        request,
        "virtuallab/manage_lab_resources.html",
        {
            "lab": lab,
            "resources": resources,
            "active_resource_count": active_resource_count,
            "resource_type_count": resource_type_count,
        },
    )


@login_required
def add_lab_resource(request, lab_id):
    """
    Add a resource to a Virtual Lab.
    """

    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to add Virtual Lab resources."
        )
        return redirect("virtuallab:lab_catalog")

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id,
    )

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        resource_type = request.POST.get(
            "resource_type",
            "FILE"
        ).strip()

        uploaded_file = request.FILES.get(
            "file"
        )

        if not title:
            messages.error(
                request,
                "Resource title is required."
            )

            return render(
                request,
                "virtuallab/add_lab_resource.html",
                {
                    "lab": lab,
                    "resource_types": LabResource.RESOURCE_TYPE_CHOICES,
                },
            )

        if not uploaded_file:
            messages.error(
                request,
                "Please select a file to upload."
            )

            return render(
                request,
                "virtuallab/add_lab_resource.html",
                {
                    "lab": lab,
                    "resource_types": LabResource.RESOURCE_TYPE_CHOICES,
                },
            )

        valid_resource_types = {
            choice[0]
            for choice in LabResource.RESOURCE_TYPE_CHOICES
        }

        if resource_type not in valid_resource_types:
            resource_type = "FILE"

        LabResource.objects.create(
            lab=lab,
            title=title,
            description=description,
            resource_type=resource_type,
            file=uploaded_file,
            uploaded_by=request.user,
        )

        messages.success(
            request,
            f"Resource '{title}' added successfully."
        )

        return redirect(
            "virtuallab:manage_lab_resources",
            lab_id=lab.id,
        )

    return render(
        request,
        "virtuallab/add_lab_resource.html",
        {
            "lab": lab,
            "resource_types": LabResource.RESOURCE_TYPE_CHOICES,
        },
    )


@login_required
def delete_lab_resource(request, resource_id):
    """
    Delete a Virtual Lab resource.
    """

    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to delete Virtual Lab resources."
        )
        return redirect("virtuallab:lab_catalog")

    resource = get_object_or_404(
        LabResource,
        id=resource_id,
    )

    lab_id = resource.lab_id

    if request.method != "POST":
        return redirect(
            "virtuallab:manage_lab_resources",
            lab_id=lab_id,
        )

    resource.delete()

    messages.success(
        request,
        "Lab resource deleted successfully."
    )

    return redirect(
        "virtuallab:manage_lab_resources",
        lab_id=lab_id,
    )


@login_required
def docker_environment_management(request):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to manage Docker environments."
        )
        return redirect("virtuallab:lab_catalog")

    try:
        docker_images = VirtualLabDockerImageService.list_images()
        docker_error = None
    except Exception as exc:
        docker_images = []
        docker_error = str(exc)

    environments = (
        VirtualLabDockerEnvironment.objects
        .prefetch_related("labs")
        .order_by("environment_type", "name")
    )

    registered_images = {
        environment.docker_image
        for environment in environments
    }

    return render(
        request,
        "virtuallab/docker_environments.html",
        {
            "docker_images": docker_images,
            "docker_error": docker_error,
            "environments": environments,
            "registered_images": registered_images,
        },
    )


@login_required
def add_docker_environment(request):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to add Docker environments."
        )
        return redirect("virtuallab:lab_catalog")

    try:
        docker_images = VirtualLabDockerImageService.list_images()
    except Exception as exc:
        messages.error(
            request,
            f"Unable to read Docker images: {exc}"
        )
        docker_images = []

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        docker_image = request.POST.get("docker_image", "").strip()
        environment_type = request.POST.get(
            "environment_type",
            "PROGRAMMING"
        ).strip()
        status = request.POST.get("status", "READY").strip()
        description = request.POST.get("description", "").strip()

        default_ram = request.POST.get(
            "default_ram",
            "2048"
        ).strip()

        default_storage = request.POST.get(
            "default_storage",
            "10240"
        ).strip()

        if not name:
            messages.error(request, "Environment name is required.")
        elif not docker_image:
            messages.error(request, "Docker image is required.")
        elif not any(
            image["tag"] == docker_image
            for image in docker_images
        ):
            messages.error(
                request,
                "Selected Docker image is not available on this machine."
            )
        elif VirtualLabDockerEnvironment.objects.filter(
            docker_image=docker_image
        ).exists():
            messages.error(
                request,
                "This Docker image is already registered."
            )
        else:
            try:
                default_ram = int(default_ram or 2048)
                default_storage = int(
                    default_storage or 10240
                )
            except ValueError:
                messages.error(
                    request,
                    "RAM and storage values must be valid numbers."
                )
            else:
                valid_types = {
                    choice[0]
                    for choice in (
                        VirtualLabDockerEnvironment
                        .ENVIRONMENT_TYPE_CHOICES
                    )
                }

                valid_statuses = {
                    choice[0]
                    for choice in (
                        VirtualLabDockerEnvironment
                        .STATUS_CHOICES
                    )
                }

                if environment_type not in valid_types:
                    environment_type = "PROGRAMMING"

                if status not in valid_statuses:
                    status = "READY"

                VirtualLabDockerEnvironment.objects.create(
                    name=name,
                    environment_type=environment_type,
                    docker_image=docker_image,
                    status=status,
                    description=description,
                    default_ram=default_ram,
                    default_storage=default_storage,
                )

                messages.success(
                    request,
                    f"Docker environment '{name}' added successfully."
                )

                return redirect(
                    "virtuallab:docker_environment_management"
                )

    selected_image = request.GET.get("image", "").strip()

    return render(
        request,
        "virtuallab/add_docker_environment.html",
        {
            "docker_images": docker_images,
            "selected_image": selected_image,
            "environment_type_choices": (
                VirtualLabDockerEnvironment
                .ENVIRONMENT_TYPE_CHOICES
            ),
            "status_choices": (
                VirtualLabDockerEnvironment
                .STATUS_CHOICES
            ),
        },
    )


@login_required
def lab_manager_overview(request, lab_id):
    if not is_lab_manager(request.user):
        messages.error(
            request,
            "You do not have permission to manage Virtual Labs."
        )
        return redirect("virtuallab:lab_catalog")

    lab = get_object_or_404(
        VirtualLab.objects.select_related("docker_environment"),
        id=lab_id,
    )

    approved_students = VirtualLabAccessRequest.objects.filter(
        lab=lab,
        status="APPROVED",
    ).count()

    pending_requests = VirtualLabAccessRequest.objects.filter(
        lab=lab,
        status="PENDING",
    ).count()

    rejected_requests = VirtualLabAccessRequest.objects.filter(
        lab=lab,
        status="REJECTED",
    ).count()

    running_environments = StudentLabEnvironment.objects.filter(
        lab=lab,
        status="RUNNING",
    ).count()

    ready_environments = StudentLabEnvironment.objects.filter(
        lab=lab,
        status="READY",
    ).count()

    environment_count = StudentLabEnvironment.objects.filter(
        lab=lab,
    ).exclude(
        status="DELETED",
    ).count()

    context = {
        "lab": lab,
        "approved_students": approved_students,
        "pending_requests": pending_requests,
        "rejected_requests": rejected_requests,
        "running_environments": running_environments,
        "ready_environments": ready_environments,
        "environment_count": environment_count,
    }

    return render(
        request,
        "virtuallab/lab_manager_overview.html",
        context,
    )