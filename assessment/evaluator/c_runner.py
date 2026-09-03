import os
import subprocess
import tempfile
import time

from .base import BaseRunner, ExecutionResult


class CRunner(BaseRunner):

    IMAGE = "gcc:13"

    def run(
        self,
        code,
        input_data="",
        timeout=None
    ):

        if timeout is None:
            timeout = self.TIMEOUT

        temp_dir = tempfile.mkdtemp()

        code_file = os.path.join(
            temp_dir,
            "main.c"
        )

        try:

            with open(
                code_file,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(code)

            start_time = time.time()

            command = [
                "docker",
                "run",
                "--rm",

                "-i",

                "--cpus=0.5",
                "--memory=256m",
                "--network=none",
                "--pids-limit=64",

                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",

                "--read-only",

                # /tmp must be executable
                "--tmpfs",
                "/tmp:rw,exec,nosuid,size=64m",

                "-v",
                f"{temp_dir}:/app:ro",

                self.IMAGE,

                "sh",
                "-c",

                (
                    "gcc /app/main.c -o /tmp/main "
                    "2>/tmp/compile_error.txt; "

                    "if [ $? -ne 0 ]; then "
                    "cat /tmp/compile_error.txt; "
                    "exit 100; "
                    "fi; "

                    "chmod 755 /tmp/main; "

                    f"timeout {timeout}s /tmp/main"
                ),
            ]

            result = subprocess.run(
                command,
                input=input_data or "",
                text=True,
                capture_output=True,
                timeout=timeout + 5,
            )

            execution_time = time.time() - start_time

            # --------------------------------------------------
            # COMPILATION ERROR
            # --------------------------------------------------

            if result.returncode == 100:

                return ExecutionResult(
                    success=False,
                    output=result.stdout,
                    error=result.stdout or result.stderr,
                    compile_error=True,
                    execution_time=execution_time,
                    status="COMPILE_ERROR",
                )

            # --------------------------------------------------
            # TIMEOUT
            # --------------------------------------------------

            if result.returncode == 124:

                return ExecutionResult(
                    success=False,
                    output=result.stdout,
                    error="Execution time exceeded.",
                    timed_out=True,
                    execution_time=execution_time,
                    status="TIMEOUT",
                )

            # --------------------------------------------------
            # SUCCESS
            # --------------------------------------------------

            if result.returncode == 0:

                return ExecutionResult(
                    success=True,
                    output=result.stdout,
                    error=result.stderr,
                    execution_time=execution_time,
                    status="SUCCESS",
                )

            # --------------------------------------------------
            # RUNTIME ERROR
            # --------------------------------------------------

            return ExecutionResult(
                success=False,
                output=result.stdout,
                error=result.stderr,
                execution_time=execution_time,
                status="RUNTIME_ERROR",
            )

        except subprocess.TimeoutExpired:

            return ExecutionResult(
                success=False,
                error="Execution time exceeded.",
                timed_out=True,
                status="TIMEOUT",
            )

        except Exception as e:

            return ExecutionResult(
                success=False,
                error=str(e),
                status="ERROR",
            )

        finally:

            try:

                for filename in os.listdir(temp_dir):

                    file_path = os.path.join(
                        temp_dir,
                        filename
                    )

                    if os.path.isfile(file_path):

                        os.remove(file_path)

                os.rmdir(temp_dir)

            except Exception:
                pass