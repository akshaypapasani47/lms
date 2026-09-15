import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3.5:9b"


def evaluate_code_quality(
    question_text,
    submitted_code,
    language,
    max_marks,
    reference_answer=None,
):
    """
    Evaluate the quality of submitted programming code
    using a local Ollama model.

    This evaluator checks code quality only.
    Functional correctness is handled separately
    by the programming test-case evaluator.
    """

    # ------------------------------------------------------
    # NO CODE
    # ------------------------------------------------------

    if not submitted_code or not submitted_code.strip():

        return {
            "marks": 0,
            "max_marks": max_marks,
            "feedback": "No code submitted.",
            "status": "NO_CODE",
        }

    # ------------------------------------------------------
    # AI PROMPT
    # ------------------------------------------------------

    prompt = f"""
You are evaluating the code quality of a student's
programming solution.

Question:
{question_text}

Programming Language:
{language}

Maximum Code Quality Marks:
{max_marks}

Student Code:
{submitted_code}

Reference Solution:
{reference_answer or "Not provided"}

Evaluate ONLY the quality of the student's code.

Consider:

1. Code structure and organization
2. Readability and clarity
3. Appropriate use of programming constructs
4. Efficiency and unnecessary operations
5. Maintainability and coding practices

IMPORTANT:
- Do NOT evaluate functional correctness based only on
  whether the code produces the expected output.
- Functional correctness is evaluated separately using
  official test cases.
- Do NOT give marks simply because the code is short.
- Give fair partial marks when appropriate.
- Do not penalize the student for not exactly matching
  the reference solution.
- Judge the submitted code according to the question.

Award a score from 0 to {max_marks}.

Return ONLY valid JSON in exactly this format:

{{
    "marks": 0,
    "feedback": "Concise explanation of the code quality evaluation."
}}

Rules:
- marks must be between 0 and {max_marks}.
- marks may be a decimal value if appropriate.
- feedback must be concise.
- Do not include markdown.
- Do not include additional fields.
"""


    # ------------------------------------------------------
    # CALL OLLAMA
    # ------------------------------------------------------

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=180,
        )

        response.raise_for_status()

        data = response.json()

        result_text = data.get(
            "response",
            ""
        )

        # Some Qwen responses may place the
        # generated JSON in "thinking".
        if not result_text:

            result_text = data.get(
                "thinking",
                ""
            )

        if not result_text:

            return {
                "marks": 0,
                "max_marks": max_marks,
                "feedback": (
                    "AI returned an empty response."
                ),
                "status": "AI_EMPTY_RESPONSE",
            }


        # --------------------------------------------------
        # PARSE JSON
        # --------------------------------------------------

        result = json.loads(
            result_text
        )


        # --------------------------------------------------
        # GET MARKS
        # --------------------------------------------------

        marks = float(
            result.get(
                "marks",
                0
            )
        )

        marks = max(
            0,
            min(
                marks,
                max_marks
            )
        )


        # --------------------------------------------------
        # RETURN RESULT
        # --------------------------------------------------

        return {

            "marks":
                marks,

            "max_marks":
                max_marks,

            "feedback":
                result.get(
                    "feedback",
                    "Code quality evaluated."
                ),

            "status":
                "EVALUATED",
        }


    # ------------------------------------------------------
    # REQUEST ERROR
    # ------------------------------------------------------

    except requests.RequestException as error:

        return {

            "marks":
                0,

            "max_marks":
                max_marks,

            "feedback":
                f"Could not connect to Ollama: {str(error)}",

            "status":
                "OLLAMA_CONNECTION_ERROR",
        }


    # ------------------------------------------------------
    # JSON ERROR
    # ------------------------------------------------------

    except json.JSONDecodeError as error:

        return {

            "marks":
                0,

            "max_marks":
                max_marks,

            "feedback":
                f"AI returned invalid JSON: {str(error)}",

            "status":
                "AI_INVALID_JSON",
        }


    # ------------------------------------------------------
    # OTHER ERROR
    # ------------------------------------------------------

    except Exception as error:

        return {

            "marks":
                0,

            "max_marks":
                max_marks,

            "feedback":
                f"AI evaluation failed: {str(error)}",

            "status":
                "AI_ERROR",
        }