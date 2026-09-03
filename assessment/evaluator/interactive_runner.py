import os
import queue
import subprocess
import tempfile
import threading
import time
import uuid

from .base import BaseRunner


class InteractiveSession:
    """
    Represents one running interactive programming session.

    The process stays alive while the student sends input.
    """

    MAX_SESSION_TIME = 60
    IDLE_TIMEOUT = 30

    def __init__(self, process, temp_dir):
        self.process = process
        self.temp_dir = temp_dir
        self.session_id = str(uuid.uuid4())

        self.created_at = time.time()
        self.last_activity = time.time()

        self.output_queue = queue.Queue()

        self.finished = False
        self.stopped = False

        self.lock = threading.Lock()

        self.reader_thread = threading.Thread(
            target=self._read_output,
            daemon=True,
        )

        self.reader_thread.start()

    def _read_output(self):
        """
        Continuously read output from the Docker process.

        Reading one byte at a time is intentional because interactive
        programs may print prompts without a newline.
        """

        try:
            while True:

                if self.process.stdout is None:
                    break

                data = self.process.stdout.read(1)

                if not data:
                    break

                if isinstance(data, bytes):
                    data = data.decode(
                        "utf-8",
                        errors="replace",
                    )

                self.output_queue.put(data)

                self.last_activity = time.time()

        except Exception as error:
            self.output_queue.put(
                f"\n[Runner error: {error}]\n"
            )

        finally:
            self.finished = True

    def read_output(self):
        """
        Return all currently available output.
        """

        output = []

        while True:
            try:
                output.append(
                    self.output_queue.get_nowait()
                )
            except queue.Empty:
                break

        return "".join(output)

    def send_input(self, input_data):
        """
        Send one input value to the running program.

        A newline is added because this represents the student
        pressing Enter.
        """

        if self.finished or self.stopped:
            return False, "Program is no longer running."

        if self.process.stdin is None:
            return False, "Program input is unavailable."

        try:

            if not input_data.endswith("\n"):
                input_data += "\n"

            data = input_data.encode("utf-8")

            with self.lock:

                self.process.stdin.write(data)
                self.process.stdin.flush()

            self.last_activity = time.time()

            return True, ""

        except (BrokenPipeError, OSError) as error:

            self.finished = True

            return False, str(error)

        except Exception as error:

            return False, str(error)

    def is_expired(self):
        """
        Check both total session lifetime and idle timeout.
        """

        now = time.time()

        if now - self.created_at > self.MAX_SESSION_TIME:
            return True

        if now - self.last_activity > self.IDLE_TIMEOUT:
            return True

        return False

    def is_running(self):
        """
        Check whether the Docker process is still alive.
        """

        if self.stopped:
            return False

        if self.process.poll() is None:
            return True

        self.finished = True

        return False

    def stop(self):
        """
        Terminate the process and clean temporary files.
        """

        if self.stopped:
            return

        self.stopped = True

        try:

            if self.process.poll() is None:

                self.process.terminate()

                try:
                    self.process.wait(timeout=2)

                except subprocess.TimeoutExpired:

                    self.process.kill()

                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass

        except Exception:
            pass

        finally:

            self._cleanup_temp_dir()

    def _cleanup_temp_dir(self):

        if not self.temp_dir:
            return

        try:

            for filename in os.listdir(self.temp_dir):

                file_path = os.path.join(
                    self.temp_dir,
                    filename,
                )

                if os.path.isfile(file_path):

                    try:
                        os.remove(file_path)
                    except Exception:
                        pass

            try:
                os.rmdir(self.temp_dir)
            except Exception:
                pass

        except Exception:
            pass


class InteractiveRunner(BaseRunner):
    """
    Starts a programming process that remains alive and accepts
    multiple inputs.

    This is separate from PythonRunner, CRunner, CPPRunner and
    JavaRunner because those runners are designed for one-shot
    execution and official test-case evaluation.
    """

    IMAGES = {
        "PYTHON": "python:3.12-slim",
        "C": "gcc:13",
        "CPP": "gcc:13",
        "JAVA": "eclipse-temurin:17-jdk",
    }

    def start(self, code, language):
        """
        Start an interactive Docker process.

        Returns:
            InteractiveSession
        """

        if not code or not code.strip():
            raise ValueError(
                "Please write some code first."
            )

        if language not in self.IMAGES:
            raise ValueError(
                f"Unsupported programming language: {language}"
            )

        temp_dir = tempfile.mkdtemp()

        try:

            code_filename = self._get_code_filename(
                language
            )

            code_file = os.path.join(
                temp_dir,
                code_filename,
            )

            with open(
                code_file,
                "w",
                encoding="utf-8",
            ) as file:

                file.write(code)

            command = self._build_command(
                language,
                temp_dir,
            )

            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )

            return InteractiveSession(
                process=process,
                temp_dir=temp_dir,
            )

        except Exception:

            self._cleanup_temp_dir(temp_dir)

            raise

    def _get_code_filename(self, language):

        filenames = {
            "PYTHON": "main.py",
            "C": "main.c",
            "CPP": "main.cpp",
            "JAVA": "Main.java",
        }

        return filenames[language]

    def _build_command(self, language, temp_dir):

        image = self.IMAGES[language]

        security_args = self.docker_security_args()

        # ---------------------------------------------------------
        # Python
        # ---------------------------------------------------------

        if language == "PYTHON":

            return [
                "docker",
                "run",
                "--rm",
                "-i",
                # "-t",

                *security_args,

                "-v",
                f"{temp_dir}:/app:ro",

                image,

                "sh",
                "-c",

                (
                    "timeout 60s "
                    "python -u /app/main.py"
                ),
            ]

        # ---------------------------------------------------------
        # C
        # ---------------------------------------------------------

        if language == "C":

            return [
                "docker",
                "run",
                "--rm",
                "-i",
                # "-t",

                "--cpus=0.5",
                "--memory=256m",
                "--network=none",
                "--pids-limit=64",

                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",

                "--read-only",

                "--tmpfs",
                "/tmp:rw,exec,nosuid,size=64m",

                "-v",
                f"{temp_dir}:/app:ro",

                image,

                "sh",
                "-c",

                (
                    "gcc /app/main.c "
                    "-o /tmp/main "
                    "2>/tmp/compile_error.txt; "

                    "if [ $? -ne 0 ]; then "
                    "cat /tmp/compile_error.txt; "
                    "exit 100; "
                    "fi; "

                    "chmod 755 /tmp/main; "

                    "timeout 60s /tmp/main"
                ),
            ]

        # ---------------------------------------------------------
        # C++
        # ---------------------------------------------------------

        if language == "CPP":

            return [
                "docker",
                "run",
                "--rm",
                "-i",
                #"-t",

                "--cpus=0.5",
                "--memory=256m",
                "--network=none",
                "--pids-limit=64",

                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",

                "--read-only",

                "--tmpfs",
                "/tmp:rw,exec,nosuid,size=64m",

                "-v",
                f"{temp_dir}:/app:ro",

                image,

                "sh",
                "-c",

                (
                    "g++ -std=c++17 "
                    "/app/main.cpp "
                    "-o /tmp/main "
                    "2>/tmp/compile_error.txt; "

                    "if [ $? -ne 0 ]; then "
                    "cat /tmp/compile_error.txt; "
                    "exit 100; "
                    "fi; "

                    "chmod 755 /tmp/main; "

                    "timeout 60s /tmp/main"
                ),
            ]

        # ---------------------------------------------------------
        # Java
        # ---------------------------------------------------------

        if language == "JAVA":

            return [
                "docker",
                "run",
                "--rm",
                "-i",
                # "-t",

                *security_args,

                "-v",
                f"{temp_dir}:/app:ro",

                image,

                "sh",
                "-c",

                (
                    "mkdir -p /tmp/java_classes; "

                    "javac /app/Main.java "
                    "-d /tmp/java_classes "
                    "2>/tmp/compile_error.txt; "

                    "if [ $? -ne 0 ]; then "
                    "cat /tmp/compile_error.txt; "
                    "exit 100; "
                    "fi; "

                    "timeout 60s "
                    "java -cp /tmp/java_classes Main"
                ),
            ]

        raise ValueError(
            f"Unsupported programming language: {language}"
        )

    @staticmethod
    def _cleanup_temp_dir(temp_dir):

        if not temp_dir:
            return

        try:

            for filename in os.listdir(temp_dir):

                file_path = os.path.join(
                    temp_dir,
                    filename,
                )

                if os.path.isfile(file_path):

                    try:
                        os.remove(file_path)
                    except Exception:
                        pass

            try:
                os.rmdir(temp_dir)
            except Exception:
                pass

        except Exception:
            pass