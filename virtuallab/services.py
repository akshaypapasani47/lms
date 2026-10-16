import uuid
from pathlib import Path
import secrets
import docker
from docker.errors import DockerException, ImageNotFound

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    VirtualLabAccessRequest,
    StudentLabEnvironment,
    LabSession,
)
class VirtualLabAccessService:

    @staticmethod
    def has_active_access(student, lab):

        return VirtualLabAccessRequest.objects.filter(
            student=student,
            lab=lab,
            status="APPROVED",
        ).exists()


    @staticmethod
    def get_pending_request(student, lab):

        return VirtualLabAccessRequest.objects.filter(
            student=student,
            lab=lab,
            status="PENDING",
        ).first()


    @staticmethod
    @transaction.atomic
    def create_request(student, lab):

        if not lab:
            raise ValueError(
                "Virtual lab was not found."
            )

        if lab.status != "ACTIVE":
            raise ValueError(
                "This virtual lab is currently inactive."
            )

        if VirtualLabAccessService.has_active_access(
            student,
            lab,
        ):
            raise ValueError(
                "You already have access to this virtual lab."
            )

        existing_request = (
            VirtualLabAccessService.get_pending_request(
                student,
                lab,
            )
        )

        if existing_request:
            raise ValueError(
                "You already have a pending access request "
                "for this lab."
            )

        request = VirtualLabAccessRequest.objects.create(
            student=student,
            lab=lab,
            status="PENDING",
        )

        return request


    @staticmethod
    def approve_request(access_request, reviewer, reason=""):

        if not access_request:
            raise ValueError("Access request was not found.")

        if access_request.status != "PENDING":
            raise ValueError(
                "Only pending access requests can be approved."
            )

        lab = access_request.lab
        student = access_request.student

        if lab.status != "ACTIVE":
            raise ValueError(
                "This virtual lab is currently inactive."
            )

        # -------------------------------------------------
        # DATABASE APPROVAL
        # -------------------------------------------------

        with transaction.atomic():

            access_request.status = "APPROVED"
            access_request.reviewed_by = reviewer
            access_request.reviewed_at = timezone.now()
            access_request.review_reason = reason or ""

            access_request.save(
                update_fields=[
                    "status",
                    "reviewed_by",
                    "reviewed_at",
                    "review_reason",
                ]
            )

            environment, created = (
                StudentLabEnvironment.objects.get_or_create(
                    student=student,
                    lab=lab,
                    defaults={
                        "status": "PROVISIONING"
                    },
                )
            )

            # Re-provision an environment that was previously deleted.
            if (
                not created
                and environment.status == "DELETED"
            ):

                environment.status = "PROVISIONING"

                environment.container_name = ""
                environment.container_id = ""
                environment.workspace_path = ""

                environment.save(
                    update_fields=[
                        "status",
                        "container_name",
                        "container_id",
                        "workspace_path",
                        "updated_at",
                    ]
                )

        # -------------------------------------------------
        # DOCKER PROVISIONING
        # -------------------------------------------------

        try:

            environment = (
                VirtualLabEnvironmentService
                .provision_environment(environment)
            )

        except Exception as exc:

            raise ValueError(
                "Access was approved, but the virtual lab "
                "environment could not be provisioned. "
                f"Environment status: ERROR. Details: {exc}"
            ) from exc

        return access_request, environment

    @staticmethod
    @transaction.atomic
    def reject_request(
        access_request,
        reviewer,
        reason="",
    ):

        if not access_request:
            raise ValueError(
                "Access request was not found."
            )

        if access_request.status != "PENDING":
            raise ValueError(
                "Only pending access requests "
                "can be rejected."
            )

        access_request.status = "REJECTED"

        access_request.reviewed_by = reviewer

        access_request.reviewed_at = timezone.now()

        access_request.review_reason = reason or ""

        access_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "review_reason",
            ]
        )

        return access_request


    @staticmethod
    @transaction.atomic
    def cancel_request(
        access_request,
        student,
    ):

        if not access_request:
            raise ValueError(
                "Access request was not found."
            )

        if access_request.student_id != student.id:
            raise PermissionError(
                "You cannot cancel another student's request."
            )

        if access_request.status != "PENDING":
            raise ValueError(
                "Only pending access requests "
                "can be cancelled."
            )

        access_request.status = "CANCELLED"

        access_request.save(
            update_fields=[
                "status",
            ]
        )

        return access_request


    @staticmethod
    def get_student_request_status(
        student,
        lab,
    ):

        if VirtualLabAccessService.has_active_access(
            student,
            lab,
        ):
            return "ACCESS_GRANTED"

        request = (
            VirtualLabAccessRequest.objects
            .filter(
                student=student,
                lab=lab,
            )
            .order_by("-requested_at")
            .first()
        )

        if not request:
            return "NO_REQUEST"

        if request.status == "PENDING":
            return "REQUEST_PENDING"

        if request.status == "REJECTED":
            return "REQUEST_REJECTED"

        if request.status == "CANCELLED":
            return "REQUEST_CANCELLED"

        return "NO_REQUEST"


class VirtualLabEnvironmentService:

    DEFAULT_IMAGE = "lms-virtual-lab:latest"

    @staticmethod
    def _get_docker_client():
        """
        Create and validate a Docker client using the
        Docker environment available on the host machine.
        """
        try:
            client = docker.from_env()
            client.ping()
            return client

        except DockerException as exc:
            raise RuntimeError(
                f"Docker is not available: {exc}"
            ) from exc


    @staticmethod
    def _get_workspace_path(environment):
        """
        Create a dedicated host workspace for one
        student's virtual lab environment.
        """

        workspace_root = (
            Path(settings.BASE_DIR)
            / "virtual_lab_workspaces"
        )

        workspace_path = (
            workspace_root
            / f"student_{environment.student_id}"
            / f"lab_{environment.lab_id}"
        )

        workspace_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return workspace_path


    @staticmethod
    def _get_container_name(environment):
        """
        Generate a unique and Docker-safe container name.
        """

        unique_id = uuid.uuid4().hex[:8]

        return (
            f"vlab_"
            f"student_{environment.student_id}_"
            f"lab_{environment.lab_id}_"
            f"{unique_id}"
        )


    @staticmethod
    @transaction.atomic
    def provision_environment(environment):
        """
        Create and start the Docker environment associated
        with a StudentLabEnvironment record.
        """

        if not environment:
            raise ValueError(
                "Virtual lab environment was not provided."
            )


        lab = environment.lab


        if lab.status != "ACTIVE":
            raise ValueError(
                "This virtual lab is not active."
            )


        # -------------------------------------------------
        # Already provisioned
        # -------------------------------------------------

        if environment.status in {
            "READY",
            "RUNNING",
        } and environment.container_id:

            return environment


        # -------------------------------------------------
        # Mark as provisioning
        # -------------------------------------------------

        environment.status = "PROVISIONING"

        environment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


        client = None
        container = None


        try:

            # -------------------------------------------------
            # Docker connection
            # -------------------------------------------------

            client = (
                VirtualLabEnvironmentService
                ._get_docker_client()
            )


            # -------------------------------------------------
            # Workspace
            # -------------------------------------------------

            workspace_path = (
                VirtualLabEnvironmentService
                ._get_workspace_path(environment)
            )


            # -------------------------------------------------
            # Container name
            # -------------------------------------------------

            container_name = (
                VirtualLabEnvironmentService
                ._get_container_name(environment)
            )


            # -------------------------------------------------
            # Docker image
            # -------------------------------------------------

            # Use the Docker Environment configured for this lab.
            # Fall back to the existing global image for older labs
            # that do not have a Docker Environment assigned.

            if lab.docker_environment:
                image = lab.docker_environment.docker_image
            else:
                image = getattr(
                    settings,
                    "VIRTUAL_LAB_DOCKER_IMAGE",
                    VirtualLabEnvironmentService.DEFAULT_IMAGE,
                )

            try:
                client.images.get(image)

            except ImageNotFound:
                client.images.pull(image)


          
            # -------------------------------------------------
            # Container command for the selected lab type
            # -------------------------------------------------

            
            if lab.lab_type == "AI":
                # Generate a unique token for this student's AI environment.
                jupyter_token = secrets.token_urlsafe(32)

                container_command = [
                    "jupyter",
                    "lab",
                    "--ip=0.0.0.0",
                    "--port=8888",
                    "--no-browser",
                    "--ServerApp.allow_root=True",
                    "--ServerApp.root_dir=/workspace",
                    f"--IdentityProvider.token={jupyter_token}",
                ]

                container_ports = None
            else:
                container_command = [
                    "/bin/sh",
                    "-c",
                    "while true; do sleep 3600; done",
                ]
                container_ports = None


            # -------------------------------------------------
            # Create container
            # -------------------------------------------------


            container = client.containers.create(

                image=image,

                name=container_name,

                command=container_command,

                ports=container_ports,

                working_dir="/workspace",

                volumes={
                    str(workspace_path): {
                        "bind": "/workspace",
                        "mode": "rw",
                    }
                },

                mem_limit=f"{lab.allocated_ram}m",

                labels={
                    "lms.virtual_lab": str(lab.id),
                    "lms.student": str(environment.student_id),
                    "lms.environment": str(environment.id),
                },
            )


            # -------------------------------------------------
            # Start container
            # -------------------------------------------------

            container.start()


            # -------------------------------------------------
            # Store environment information
            # -------------------------------------------------

            environment.container_name = (
                container.name
            )

            environment.container_id = (
                container.id
            )

            environment.workspace_path = (
                str(workspace_path)
            )

            
            if lab.lab_type == "AI":
                environment.jupyter_token = jupyter_token


            environment.status = "READY"

            environment.last_started_at = (
                timezone.now()
            )

            environment.save(  
                update_fields=[
                    "container_name",
                    "container_id",
                    "workspace_path",
                    "jupyter_token",
                    "status",
                    "last_started_at",
                    "updated_at",
                ]
            )


            return environment


        except Exception:

            # -------------------------------------------------
            # Cleanup partially created container
            # -------------------------------------------------

            if container is not None:

                try:
                    container.remove(
                        force=True
                    )

                except DockerException:
                    pass


            environment.status = "ERROR"

            environment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            raise




# =========================================================
# VIRTUAL LAB SESSION SERVICE
# =========================================================

class VirtualLabSessionService:

    @staticmethod
    @transaction.atomic
    def open_session(
        student,
        lab,
        client_ip=None,
    ):
        """
        Open or reuse the student's active virtual lab session.

        Access permission, environment readiness and session
        lifecycle are deliberately kept separate.
        """

        if not student:
            raise ValueError(
                "Student was not provided."
            )

        if not lab:
            raise ValueError(
                "Virtual lab was not provided."
            )

        # -------------------------------------------------
        # LAB STATE
        # -------------------------------------------------

        if lab.status != "ACTIVE":
            raise ValueError(
                "This virtual lab is currently inactive."
            )

        # -------------------------------------------------
        # ACCESS STATE
        # -------------------------------------------------

        has_access = (
            VirtualLabAccessRequest.objects
            .filter(
                student=student,
                lab=lab,
                status="APPROVED",
            )
            .exists()
        )

        if not has_access:
            raise ValueError(
                "You do not have approved access "
                "to this virtual lab."
            )

        # -------------------------------------------------
        # ENVIRONMENT STATE
        # -------------------------------------------------

        environment = (
            StudentLabEnvironment.objects
            .filter(
                student=student,
                lab=lab,
            )
            .first()
        )

        if not environment:
            raise ValueError(
                "Your virtual lab environment "
                "has not been provisioned yet."
            )

        if environment.status not in {
            "READY",
            "RUNNING",
        }:
            raise ValueError(
                "Your virtual lab environment "
                f"is not ready. Current status: "
                f"{environment.status}."
            )

        # -------------------------------------------------
        # EXISTING ACTIVE SESSION
        # -------------------------------------------------

        active_session = (
            LabSession.objects
            .filter(
                student=student,
                lab=lab,
                status="ACTIVE",
            )
            .first()
        )

        if active_session:

            active_session.last_activity = timezone.now()

            if client_ip:
                active_session.client_ip = client_ip

            active_session.environment = environment

            active_session.save(
                update_fields=[
                    "last_activity",
                    "client_ip",
                    "environment",
                ]
            )

            return active_session

        # -------------------------------------------------
        # CREATE NEW SESSION
        # -------------------------------------------------

        session = LabSession.objects.create(
            student=student,
            lab=lab,
            environment=environment,
            status="ACTIVE",
            last_activity=timezone.now(),
            client_ip=client_ip,
        )

        return session


    @staticmethod
    @transaction.atomic
    def touch_session(session):
        """
        Update the last activity timestamp for an active session.
        """

        if not session:
            raise ValueError(
                "Lab session was not provided."
            )

        if session.status != "ACTIVE":
            raise ValueError(
                "Only active sessions can be updated."
            )

        session.last_activity = timezone.now()

        session.save(
            update_fields=[
                "last_activity",
            ]
        )

        return session


    @staticmethod
    @transaction.atomic
    def close_session(session):
        """
        Close a student's active session.

        Closing the session does NOT delete or stop the
        student's compute environment.
        """

        if not session:
            raise ValueError(
                "Lab session was not provided."
            )

        if session.status != "ACTIVE":

            return session

        now = timezone.now()

        session.closed_at = now
        session.status = "CLOSED"

        session.duration_seconds = (
            session.calculate_duration()
        )

        session.last_activity = now

        session.save(
            update_fields=[
                "closed_at",
                "status",
                "duration_seconds",
                "last_activity",
            ]
        )

        return session


class VirtualLabTerminalService:

    MAX_OUTPUT_LENGTH = 12000

    ALLOWED_SIMPLE_COMMANDS = {
        "pwd",
        "ls",
        "ls -la",
        "ls -l",
        "python --version",
        "python -V",
        "pip --version",
        "whoami",
    }

    @staticmethod
    def _get_container(environment):

        if not environment:
            raise ValueError(
                "Virtual lab environment was not found."
            )

        if environment.status not in {"READY", "RUNNING"}:
            raise ValueError(
                "Virtual lab environment is not ready."
            )

        if not environment.container_id:
            raise ValueError(
                "Docker container is not configured."
            )

        client = (
            VirtualLabEnvironmentService
            ._get_docker_client()
        )

        try:
            container = client.containers.get(
                environment.container_id
            )
        except Exception as exc:
            raise ValueError(
                "Virtual lab container could not be found."
            ) from exc

        return container

    @staticmethod
    def _validate_python_command(command):

        parts = command.strip().split()

        if len(parts) != 2:
            return None

        if parts[0] != "python":
            return None

        filename = parts[1].strip()

        if not filename:
            return None

        if (
            "/" in filename
            or "\\" in filename
            or ".." in filename
            or not filename.endswith(".py")
        ):
            return None

        return filename

    @staticmethod
    def execute_command(
        environment,
        command,
    ):

        command = str(command or "").strip()

        if not command:
            raise ValueError(
                "Enter a command."
            )

        container = (
            VirtualLabTerminalService
            ._get_container(environment)
        )

        python_filename = (
            VirtualLabTerminalService
            ._validate_python_command(command)
        )


        
        # HPC labs need normal Linux shell commands.
        # Keep the existing allowlist for other labs.
        if environment.lab.lab_type == "HPC":
            if len(command) > 1000:
                raise ValueError(
                    "Command exceeds the 1000-character limit."
                )

            exec_command = [
                "/usr/bin/timeout",
                "30s",
                "/bin/bash",
                "-lc",
                command,
            ]

        elif command in (
            VirtualLabTerminalService
            .ALLOWED_SIMPLE_COMMANDS
        ):

            exec_command = [
                "/bin/sh",
                "-lc",
                command,
            ]

        elif python_filename:

            exec_command = [
                "/bin/sh",
                "-lc",
                (
                    "timeout 10s "
                    "python "
                    f"'/workspace/{python_filename}'"
                ),
            ]

        else:

            raise ValueError(
                "Command is not allowed in this terminal version."
            )



        if command in (
            VirtualLabTerminalService
            .ALLOWED_SIMPLE_COMMANDS
        ):

            exec_command = [
                "/bin/sh",
                "-lc",
                command,
            ]

        elif python_filename:

            exec_command = [
                "/bin/sh",
                "-lc",
                (
                    "timeout 10s "
                    "python "
                    f"'/workspace/{python_filename}'"
                ),
            ]

        else:

            raise ValueError(
                "Command is not allowed in this terminal version."
            )

        try:

            result = container.exec_run(
                exec_command,
                workdir="/workspace",
                stdout=True,
                stderr=True,
                demux=True,
            )

        except Exception as exc:

            raise ValueError(
                f"Command execution failed: {exc}"
            ) from exc

        stdout = ""
        stderr = ""

        if result.output:

            output = result.output

            if isinstance(output, tuple):

                raw_stdout, raw_stderr = output

                if raw_stdout:
                    stdout = raw_stdout.decode(
                        "utf-8",
                        errors="replace",
                    )

                if raw_stderr:
                    stderr = raw_stderr.decode(
                        "utf-8",
                        errors="replace",
                    )

            elif isinstance(output, bytes):

                stdout = output.decode(
                    "utf-8",
                    errors="replace",
                )

        combined_output = (
            stdout + stderr
        )

        if len(combined_output) > (
            VirtualLabTerminalService
            .MAX_OUTPUT_LENGTH
        ):

            combined_output = (
                combined_output[
                    :VirtualLabTerminalService
                    .MAX_OUTPUT_LENGTH
                ]
                + "\n\n[OUTPUT TRUNCATED]"
            )

        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "output": combined_output,
            "exit_code": result.exit_code,
            "success": result.exit_code == 0,
        }

class VirtualLabDockerImageService:
    """
    Discovers Docker images available on the host machine.
    """

    @staticmethod
    def get_client():
        return docker.from_env()

    @classmethod
    def list_images(cls):
        client = cls.get_client()

        images = []

        for image in client.images.list():
            tags = image.tags or []

            for tag in tags:
                images.append({
                    "id": image.id,
                    "tag": tag,
                    "short_id": image.short_id,
                })

        return sorted(
            images,
            key=lambda item: item["tag"].lower(),
        )