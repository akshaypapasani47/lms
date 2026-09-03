from .python_runner import PythonRunner
from .c_runner import CRunner
from .cpp_runner import CPPRunner
from .java_runner import JavaRunner


RUNNERS = {
    "PYTHON": PythonRunner,
    "C": CRunner,
    "CPP": CPPRunner,
    "JAVA": JavaRunner,
}


def get_runner(language):

    runner_class = RUNNERS.get(language)

    if not runner_class:

        raise ValueError(
            f"Unsupported programming language: {language}"
        )

    return runner_class()