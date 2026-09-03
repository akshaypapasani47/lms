import os
import subprocess
import tempfile
import time

from .base import BaseRunner, ExecutionResult


class PythonRunner(BaseRunner):

    IMAGE = "python:3.12-slim"

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
            "main.py"
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

                # IMPORTANT:
                # Attach stdin so input() works.
                "-i",

                *self.docker_security_args(),

                "-v",
                f"{temp_dir}:/app:ro",

                self.IMAGE,

                "timeout",
                f"{timeout}s",

                "python",
                "/app/main.py",
            ]

            result = subprocess.run(
                command,
                input=input_data or "",
                text=True,
                capture_output=True,
                timeout=timeout + 5,
            )

            execution_time = time.time() - start_time

            # timeout command returns 124
            if result.returncode == 124:

                return ExecutionResult(
                    success=False,
                    output=result.stdout,
                    error="Execution time exceeded.",
                    timed_out=True,
                    execution_time=execution_time,
                    status="TIMEOUT",
                )

            # Successful execution
            if result.returncode == 0:

                return ExecutionResult(
                    success=True,
                    output=result.stdout,
                    error=result.stderr,
                    execution_time=execution_time,
                    status="SUCCESS",
                )

            # Runtime error
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