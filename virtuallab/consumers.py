import json
import threading
import time
import shlex
import uuid
from pathlib import Path
import re
import docker
from docker.errors import DockerException, NotFound

from channels.generic.websocket import WebsocketConsumer

from .models import VirtualLab, LabSession
from .services import VirtualLabSessionService


class VirtualLabTerminalConsumer(WebsocketConsumer):
    """Persistent interactive Docker terminal for a Virtual Lab session."""

    def connect(self):
        self.client = None
        self.container = None
        self.docker_socket = None
        self.exec_id = None
        self.reader_thread = None
        self.running = False
        self.last_activity = time.time()

        self.user = self.scope.get("user")
        self.lab_id = self.scope["url_route"]["kwargs"]["lab_id"]

        if not self.user or not self.user.is_authenticated:
            self.close(code=4001)
            return

        try:
            self.lab = VirtualLab.objects.get(
                id=self.lab_id,
                status="ACTIVE",
            )

            self.session = (
                LabSession.objects
                .select_related("lab", "environment")
                .filter(
                    student=self.user,
                    lab=self.lab,
                    status="ACTIVE",
                )
                .first()
            )

            if not self.session:
                self.close(code=4003)
                return

            self.environment = self.session.environment

            if not self.environment:
                self.close(code=4004)
                return

            if self.environment.status not in {"READY", "RUNNING"}:
                self.close(code=4005)
                return

            if not self.environment.container_id:
                self.close(code=4006)
                return

            self.client = docker.from_env()
            self.client.ping()

            self.container = self.client.containers.get(
                self.environment.container_id
            )
            self.container.reload()

            if self.container.status != "running":
                self.close(code=4007)
                return

            self.accept()
            self.create_shell()
            self.running = True
            self.touch_session()

            self.send(
                text_data=json.dumps(
                    {
                        "type": "connected",
                        "lab": self.lab.name,
                        "container": self.container.name,
                        "workspace": "/workspace",
                    }
                )
            )

            self.reader_thread = threading.Thread(
                target=self.read_output,
                daemon=True,
            )
            self.reader_thread.start()

        except VirtualLab.DoesNotExist:
            self.close(code=4004)

        except NotFound:
            self.close(code=4008)

        except DockerException as exc:
            print("VIRTUAL LAB DOCKER ERROR:", exc)
            self.close(code=4009)

        except Exception as exc:
            print("VIRTUAL LAB TERMINAL ERROR:", exc)
            try:
                self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": str(exc),
                        }
                    )
                )
            except Exception:
                pass
            self.close(code=4010)

    def create_shell(self):
        """Create a real interactive bash process with a PTY."""
        self.exec_id = self.client.api.exec_create(
            self.container.id,
            cmd=[
                "/bin/bash",
                "--login",
                "-c",
                "cd /workspace && exec /bin/bash --login",
            ],
            stdin=True,
            tty=True,
            environment={
                "TERM": "xterm-256color",
                "COLORTERM": "truecolor",
            },
        )["Id"]

        self.docker_socket = self.client.api.exec_start(
            self.exec_id,
            tty=True,
            socket=True,
            detach=False,
        )

    def receive(self, text_data):
        self.last_activity = time.time()

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            self.send_to_shell(text_data)
            return

        if data.get("type") == "input":
            terminal_input = data.get("data", "")
            if terminal_input:
                self.send_to_shell(terminal_input)
                self.touch_session()
            return

        if data.get("type") == "resize":
            try:
                cols = max(20, int(data.get("cols", 120)))
                rows = max(5, int(data.get("rows", 30)))
                self.resize_terminal(cols, rows)
            except (TypeError, ValueError):
                pass
            return

        if data.get("type") == "heartbeat":
            self.touch_session()

    def send_to_shell(self, data):
        if not self.docker_socket:
            return

        try:
            self.docker_socket.send(
                data.encode("utf-8", errors="ignore")
            )
        except Exception as exc:
            print("TERMINAL INPUT ERROR:", exc)
            self.close()

    def resize_terminal(self, cols, rows):
        if not self.exec_id or not self.client:
            return

        try:
            self.client.api.exec_resize(
                self.exec_id,
                height=rows,
                width=cols,
            )
        except Exception as exc:
            print("TERMINAL RESIZE ERROR:", exc)

    def read_output(self):
        while self.running:
            try:
                output = self.docker_socket.recv(8192)

                if not output:
                    break

                if isinstance(output, bytes):
                    output = output.decode(
                        "utf-8",
                        errors="replace",
                    )

                self.send(
                    text_data=json.dumps(
                        {
                            "type": "output",
                            "data": output,
                        }
                    )
                )

            except Exception as exc:
                print("TERMINAL OUTPUT ERROR:", exc)
                break

        self.running = False

    def touch_session(self):
        try:
            if self.session:
                self.session = VirtualLabSessionService.touch_session(
                    self.session
                )
        except Exception as exc:
            print("SESSION TOUCH ERROR:", exc)

    def disconnect(self, close_code):
        self.running = False

        print(
            "VIRTUAL LAB TERMINAL DISCONNECTED:",
            close_code,
        )

        try:
            if self.docker_socket:
                self.docker_socket.close()
        except Exception:
            pass

        try:
            if self.client:
                self.client.close()
        except Exception:
            pass



class VirtualLabCodeRunnerConsumer(WebsocketConsumer):
    """
    Interactive code execution WebSocket.

    The browser sends:
        - program path
        - current editor content
        - keyboard input

    Docker sends:
        - live stdout/stderr
        - process completion
    """

    SUPPORTED_EXTENSIONS = {
        ".py",
        ".java",
        ".c",
        ".cpp",
        ".cc",
        ".cxx",
        ".sh",
    }

    def connect(self):
        self.client = None
        self.container = None
        self.docker_socket = None
        self.exec_id = None
        self.reader_thread = None
        self.running = False
        self.session = None
        self.environment = None
        self.last_activity = time.time()

        self.user = self.scope.get("user")
        self.lab_id = self.scope["url_route"]["kwargs"]["lab_id"]

        if not self.user or not self.user.is_authenticated:
            self.close(code=4001)
            return

        try:
            self.lab = VirtualLab.objects.get(
                id=self.lab_id,
                status="ACTIVE",
            )

            self.session = (
                LabSession.objects
                .select_related("lab", "environment")
                .filter(
                    student=self.user,
                    lab=self.lab,
                    status="ACTIVE",
                )
                .first()
            )

            if not self.session:
                self.close(code=4003)
                return

            self.environment = self.session.environment

            if not self.environment:
                self.close(code=4004)
                return

            if self.environment.status not in {
                "READY",
                "RUNNING",
            }:
                self.close(code=4005)
                return

            if not self.environment.container_id:
                self.close(code=4006)
                return

            self.client = docker.from_env()
            self.client.ping()

            self.container = self.client.containers.get(
                self.environment.container_id
            )

            self.container.reload()

            if self.container.status != "running":
                self.close(code=4007)
                return

            self.accept()

            self.send(
                text_data=json.dumps({
                    "type": "connected",
                    "lab": self.lab.name,
                })
            )

        except VirtualLab.DoesNotExist:
            self.close(code=4004)

        except NotFound:
            self.close(code=4008)

        except DockerException as exc:
            print(
                "VIRTUAL LAB CODE RUNNER DOCKER ERROR:",
                exc,
            )
            self.close(code=4009)

        except Exception as exc:
            print(
                "VIRTUAL LAB CODE RUNNER ERROR:",
                exc,
            )

            try:
                self.send(
                    text_data=json.dumps({
                        "type": "error",
                        "message": str(exc),
                    })
                )
            except Exception:
                pass

            self.close(code=4010)

    # =========================================================
    # RECEIVE MESSAGES FROM BROWSER
    # =========================================================

    def receive(self, text_data):
        self.last_activity = time.time()

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = data.get("type")

        # -----------------------------------------------------
        # START PROGRAM
        # -----------------------------------------------------

        if message_type == "start":
            if self.running:
                self.send_error(
                    "A program is already running."
                )
                return

            path = str(
                data.get("path", "")
            ).strip()

            content = data.get(
                "content",
                "",
            )

            if not isinstance(content, str):
                self.send_error(
                    "Invalid program content."
                )
                return
 
            try:
                execution_mode = data.get("execution_mode", "normal")
                mpi_processes = data.get("mpi_processes", 4)
                openmp_threads = data.get("openmp_threads", 4)

                self.start_program(
                    path,
                    content,
                    mpi_processes=mpi_processes,
                    execution_mode=execution_mode,
                    openmp_threads=openmp_threads,
                )

            except Exception as exc:
                self.send_error(str(exc))


            return

        # -----------------------------------------------------
        # PROGRAM INPUT
        # -----------------------------------------------------

        if message_type == "input":
            program_input = data.get(
                "data",
                "",
            )

            if program_input:
                self.send_to_process(
                    program_input
                )

            return

        # -----------------------------------------------------
        # STOP PROGRAM
        # -----------------------------------------------------

        if message_type == "stop":
            self.stop_program()
            return

        # -----------------------------------------------------
        # HEARTBEAT
        # -----------------------------------------------------

        if message_type == "heartbeat":
            self.touch_session()

    # =========================================================
    # START PROGRAM
    # =========================================================

    def start_program(
        self,
        relative_path,
        content,
        mpi_processes=4,
        execution_mode="normal",
        openmp_threads=4,
    ):


        is_hpc_lab = (
            getattr(self.lab, "lab_type", "") == "HPC"
        )

        allowed_modes = {"normal", "mpi", "openmp"}

        if not isinstance(execution_mode, str):
            raise ValueError("Invalid execution mode.")

        execution_mode = execution_mode.lower().strip()

        if execution_mode not in allowed_modes:
            raise ValueError("Unsupported execution mode.")

        # Keep all non-HPC labs on their existing normal mode.
        if not is_hpc_lab:
            execution_mode = "normal"

        try:
            mpi_processes = int(mpi_processes)
            openmp_threads = int(openmp_threads)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Process and thread counts must be integers."
            ) from exc

        if mpi_processes not in {1, 2, 4, 8}:
            raise ValueError("Choose 1, 2, 4, or 8 MPI processes.")

        if openmp_threads not in {1, 2, 4, 8}:
            raise ValueError("Choose 1, 2, 4, or 8 OpenMP threads.")
        # Validate MPI process count received from the browser.
        allowed_mpi_processes = {1, 2, 4, 8}

        if (
            isinstance(mpi_processes, bool)
            or not isinstance(mpi_processes, int)
            or mpi_processes not in allowed_mpi_processes
        ):
            raise ValueError(
                "MPI process count must be 1, 2, 4, or 8."
            )

        relative_path = relative_path.replace(
            "\\",
            "/",
        ).strip()

        if not relative_path:
            raise ValueError(
                "No program file was selected."
            )

        extension = (
            Path(relative_path)
            .suffix
            .lower()
        )

        
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "This file type cannot be executed."
            )

        if (
            is_hpc_lab
            and execution_mode != "normal"
            and extension != ".c"
        ):
            raise ValueError(
                "MPI and OpenMP modes require a C source file."
            )

        

        workspace = Path(
            self.environment.workspace_path
        ).resolve()

        requested_file = (
            workspace / relative_path
        ).resolve()

        try:
            requested_file.relative_to(
                workspace
            )
        except ValueError as exc:
            raise ValueError(
                "Invalid file path."
            ) from exc

        if not requested_file.parent.exists():
            raise ValueError(
                "Program directory does not exist."
            )

        # -----------------------------------------------------
        # SAVE CURRENT EDITOR CONTENT
        # -----------------------------------------------------

        # Normalize Windows / Mac line endings
        # so Linux programs receive standard Unix LF endings.
        normalized_content = (
            content
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        requested_file.write_text(
            normalized_content,
            encoding="utf-8",
            newline="\n",
        )

        container_file = (
            "/workspace/"
            + relative_path
        )

        quoted_file = shlex.quote(
            container_file
        )

        # -----------------------------------------------------
        # BUILD EXECUTION COMMAND
        # -----------------------------------------------------

        if extension == ".py":

            command = [
                "/bin/sh",
                "-c",
                (
                    "cd /workspace && "
                    "exec python3 "
                    f"{quoted_file}"
                ),
            ]

        elif extension == ".java":

            class_name = requested_file.stem

            if not class_name.isidentifier():
                raise ValueError(
                    "Java filename must contain a valid "
                    "Java class name."
                )

            java_output_dir = (
                "/tmp/"
                + f"vlab_java_{uuid.uuid4().hex}"
            )

            command = [
                "/bin/sh",
                "-c",
                (
                    "mkdir -p "
                    f"{shlex.quote(java_output_dir)} && "

                    "javac "
                    "-d "
                    f"{shlex.quote(java_output_dir)} "
                    f"{quoted_file} && "

                    "exec /usr/bin/timeout "
                    "10 "
                    "java "
                    "-cp "
                    f"{shlex.quote(java_output_dir)} "
                    f"{shlex.quote(class_name)}"
                ),
            ]

        
        
        elif extension == ".c":

            
            output_file = (
                "/tmp/"
                + f"vlab_c_{uuid.uuid4().hex}"
            )

            if execution_mode == "mpi":

                command = [
                    "/bin/sh",
                    "-c",
                    (
                        f"mpicc {quoted_file} "
                        f"-o {shlex.quote(output_file)} && "
                        "exec /usr/bin/timeout 30s "
                        f"mpirun --allow-run-as-root "
                        f"-np {mpi_processes} "
                        f"{shlex.quote(output_file)}"
                    ),
                ]

            elif execution_mode == "openmp":

                command = [
                    "/bin/sh",
                    "-c",
                    (
                        f"gcc -fopenmp {quoted_file} "
                        f"-o {shlex.quote(output_file)} && "
                        f"OMP_NUM_THREADS={openmp_threads} "
                        "exec /usr/bin/timeout 30s "
                        f"{shlex.quote(output_file)}"
                    ),
                ]

            else:

                # Normal mode preserves ordinary C execution.
                command = [
                    "/bin/sh",
                    "-c",
                    (
                        f"gcc {quoted_file} "
                        f"-o {shlex.quote(output_file)} && "
                        f"exec {shlex.quote(output_file)}"
                    ),
                ]



        elif extension in {
            ".cpp",
            ".cc",
            ".cxx",
        }:

            output_file = (
                "/tmp/"
                + f"vlab_cpp_{uuid.uuid4().hex}"
            )

            command = [
                "/bin/sh",
                "-c",
                (
                    f"g++ {quoted_file} "
                    f"-o {shlex.quote(output_file)} && "
                    f"exec {shlex.quote(output_file)}"
                ),
            ]

        elif extension == ".sh":

            command = [
                "/bin/sh",
                "-c",
                (
                    "cd /workspace && "
                    "exec /bin/bash "
                    f"{quoted_file}"
                ),
            ]

        else:
            raise ValueError(
                "Unsupported executable file."
            )

        # -----------------------------------------------------
        # CREATE INTERACTIVE DOCKER EXEC
        # -----------------------------------------------------

        self.exec_id = self.client.api.exec_create(
            self.container.id,
            cmd=command,
            stdin=True,
            tty=True,
            environment={
                "TERM": "xterm-256color",
                "COLORTERM": "truecolor",
            },
        )["Id"]

        self.docker_socket = (
            self.client.api.exec_start(
                self.exec_id,
                tty=True,
                socket=True,
                detach=False,
            )
        )

        self.running = True
        self.touch_session()

        self.send(
            text_data=json.dumps({
                "type": "started",
                "file": relative_path,
            })
        )

        # -----------------------------------------------------
        # READ DOCKER OUTPUT CONTINUOUSLY
        # -----------------------------------------------------

        self.reader_thread = threading.Thread(
            target=self.read_program_output,
            daemon=True,
        )

        self.reader_thread.start()





    # =========================================================
    # SEND INPUT TO PROGRAM
    # =========================================================

    def send_to_process(self, data):

        if not self.docker_socket:
            return

        if not self.running:
            return

        try:
            self.docker_socket.send(
                data.encode(
                    "utf-8",
                    errors="ignore",
                )
            )

            self.touch_session()

        except Exception as exc:
            print(
                "CODE RUNNER INPUT ERROR:",
                exc,
            )

    # =========================================================
    # READ PROGRAM OUTPUT
    # =========================================================

    def read_program_output(self):

        exit_code = None

        while self.running:

            try:
                output = (
                    self.docker_socket.recv(
                        8192
                    )
                )

                if not output:
                    break

                if isinstance(
                    output,
                    bytes,
                ):
                    output = output.decode(
                        "utf-8",
                        errors="replace",
                    )

                self.send(
                    text_data=json.dumps({
                        "type": "output",
                        "data": output,
                    })
                )

            except Exception as exc:

                error_text = str(exc)

                if "The pipe has been ended" in error_text:
                    print(
                        "CODE RUNNER PIPE CLOSED: "
                        "program finished."
                    )
                else:
                    print(
                        "CODE RUNNER OUTPUT ERROR:",
                        exc,
                    )

                break

        # -----------------------------------------------------
        # CHECK PROCESS RESULT
        # -----------------------------------------------------

        try:

            if self.exec_id and self.client:

                result = (
                    self.client.api
                    .exec_inspect(
                        self.exec_id
                    )
                )

                exit_code = result.get(
                    "ExitCode"
                )

        except Exception as exc:

            print(
                "CODE RUNNER INSPECT ERROR:",
                exc,
            )

        self.running = False

        self.send(
            text_data=json.dumps({
                "type": "finished",
                "exit_code": exit_code,
            })
        )

        self.touch_session()

    # =========================================================
    # STOP PROGRAM
    # =========================================================

    def stop_program(self):

        if not self.running:
            return

        try:

            # Ctrl+C through the program's stdin/TTY.
            if self.docker_socket:
                self.docker_socket.send(
                    b"\x03"
                )

        except Exception as exc:

            print(
                "CODE RUNNER STOP ERROR:",
                exc,
            )

    # =========================================================
    # ERROR
    # =========================================================

    def send_error(self, message):

        try:
            self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": message,
                })
            )
        except Exception:
            pass

    # =========================================================
    # SESSION ACTIVITY
    # =========================================================

    def touch_session(self):

        try:

            if self.session:
                self.session = (
                    VirtualLabSessionService
                    .touch_session(
                        self.session
                    )
                )

        except Exception as exc:

            print(
                "CODE RUNNER SESSION TOUCH ERROR:",
                exc,
            )

    # =========================================================
    # DISCONNECT
    # =========================================================

    def disconnect(self, close_code):

        self.running = False

        print(
            "VIRTUAL LAB CODE RUNNER DISCONNECTED:",
            close_code,
        )

        try:
            if self.docker_socket:
                self.docker_socket.send(
                    b"\x03"
                )
        except Exception:
            pass

        try:
            if self.docker_socket:
                self.docker_socket.close()
        except Exception:
            pass

        try:
            if self.client:
                self.client.close()
        except Exception:
            pass