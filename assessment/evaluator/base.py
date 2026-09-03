class ExecutionResult:

    def __init__(
        self,
        success=False,
        output="",
        error="",
        timed_out=False,
        compile_error=False,
        execution_time=0,
        status="ERROR",
    ):

        self.success = success
        self.output = output or ""
        self.error = error or ""
        self.timed_out = timed_out
        self.compile_error = compile_error
        self.execution_time = execution_time
        self.status = status


class BaseRunner:

    TIMEOUT = 5

    CPU_LIMIT = "0.5"
    MEMORY_LIMIT = "256m"
    PIDS_LIMIT = "64"

    def normalize_output(self, output):

        if output is None:
            return ""

        lines = output.strip().splitlines()

        normalized_lines = []

        for line in lines:

            normalized_lines.append(
                " ".join(line.strip().split())
            )

        return "\n".join(
            normalized_lines
        ).strip()

    def outputs_match(self, actual, expected):

        return (
            self.normalize_output(actual)
            ==
            self.normalize_output(expected)
        )

    def docker_security_args(self):

        return [
            "--cpus=" + self.CPU_LIMIT,
            "--memory=" + self.MEMORY_LIMIT,
            "--network=none",
            "--pids-limit=" + self.PIDS_LIMIT,
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,nosuid,size=64m",
        ]