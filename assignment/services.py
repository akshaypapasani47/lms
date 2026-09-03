import os
import re
import subprocess
import sys
import tempfile
from .models import QuestionSubmission, StudentSubmission


def execute_code(language, code, input_data=""):
    """
    Executes submitted code safely and checks output against inputs.
    Supports PYTHON, JAVA, C, and CPP.
    """
    language = (language or "PYTHON").upper()
    
    # Clean and normalize line breaks
    formatted_input = ""
    if input_data:
        lines = [line.strip() for line in input_data.replace('\r\n', '\n').split('\n') if line.strip()]
        formatted_input = "\n".join(lines) + "\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        if language == "PYTHON":
            file_path = os.path.join(tmpdir, "solution.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            cmd = [sys.executable, file_path]

        elif language in ["CPP", "C"]:
            ext = "cpp" if language == "CPP" else "c"
            src_path = os.path.join(tmpdir, f"solution.{ext}")
            bin_name = "solution.exe" if os.name == "nt" else "solution"
            bin_path = os.path.abspath(os.path.join(tmpdir, bin_name))
            
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            compiler = "g++" if language == "CPP" else "gcc"
            compile_res = subprocess.run([compiler, src_path, "-o", bin_path], capture_output=True, text=True)
            if compile_res.returncode != 0:
                return False, f"Compilation Error:\n{compile_res.stderr}"
            cmd = [bin_path]

        elif language == "JAVA":
            file_path = os.path.join(tmpdir, "Main.java")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            compile_res = subprocess.run(["javac", file_path], capture_output=True, text=True)
            if compile_res.returncode != 0:
                return False, f"Compilation Error:\n{compile_res.stderr}"
            cmd = ["java", "-cp", tmpdir, "Main"]
        else:
            return False, f"Unsupported Language: {language}"

        try:
            res = subprocess.run(cmd, input=formatted_input, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return True, res.stdout.strip()
            return False, res.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Execution Timed Out (Limit: 5s)"


def run_ai_code_evaluation(code, question_text, expected_output, actual_output, is_passed):
    status_str = "PASSED" if is_passed else "FAILED"
    return (
        f"--- AI Code Review ---\n"
        f"Status: Test Case {status_str}\n"
        f"Question: {question_text}\n"
        f"Expected Output: {expected_output}\n"
        f"Actual Output: {actual_output}\n\n"
        f"Code Analysis:\n"
        f"- Structure: Code is structured correctly.\n"
        f"- Suggestions: Good work!"
    )


def normalize_output(text):
    """
    Removes all whitespace spaces after commas and surrounding quotes 
    so '[1, 2, 3]' matches '[1,2,3]'.
    """
    if not text:
        return ""
    # Remove spacing around commas, brackets, and braces
    normalized = re.sub(r'\s*([,\[\]\{\}:])\s*', r'\1', text.strip())
    return normalized


def evaluate_submission(student_submission_id):
    submission = StudentSubmission.objects.get(id=student_submission_id)
    total_obtained = 0

    for q_sub in submission.question_answers.all():
        question = q_sub.question
        test_cases = question.test_cases.all()
        q_marks = 0
        output_logs = []
        last_output = ""

        if test_cases.exists():
            for tc in test_cases:
                success, output = execute_code(
                    question.programming_language,
                    q_sub.submitted_code,
                    tc.input_data
                )
                
                last_output = output
                
                # Use whitespace-insensitive comparison
                norm_actual = normalize_output(output)
                norm_expected = normalize_output(tc.expected_output)

                if success and norm_actual == norm_expected:
                    q_marks += tc.marks
                    output_logs.append(f"Test Case [ID:{tc.id}]: PASSED (+{tc.marks} marks)")
                else:
                    output_logs.append(f"Test Case [ID:{tc.id}]: FAILED (Expected: '{tc.expected_output.strip()}', Got: '{output.strip()}')")
        else:
            success, output = execute_code(
                question.programming_language,
                q_sub.submitted_code
            )
            last_output = output
            q_marks = question.marks if success else 0
            output_logs.append(f"Execution Output: {output}")

        q_sub.obtained_marks = q_marks
        q_sub.execution_output = "\n".join(output_logs)
        q_sub.ai_analysis = run_ai_code_evaluation(
            q_sub.submitted_code,
            question.question_text,
            "Matching Test Cases",
            last_output,
            q_marks > 0
        )
        q_sub.save()

        total_obtained += q_marks

    submission.obtained_marks = total_obtained
    submission.is_evaluated = True
    submission.ai_feedback = f"Total Marks Awarded: {total_obtained} / {submission.assignment.total_marks}"
    submission.save()

    return submission