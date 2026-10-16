import json

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3.5:9b"


def evaluate_theory_answer(
    question_text,
    student_answer,
    max_marks,
    reference_answer=None,
    evaluation_criteria=None,
):
    """
    Evaluate a student's theory answer using a local Ollama model.
    """

    # ----------------------------------------------------------
    # No answer
    # ----------------------------------------------------------

    if not student_answer or not student_answer.strip():

        return {
            "marks": 0,
            "max_marks": max_marks,
            "feedback": "No answer submitted.",
            "is_correct": False,
            "status": "NO_ANSWER",
        }


    # ----------------------------------------------------------
    # Build evaluation prompt
    # ----------------------------------------------------------

    prompt = f"""
You are evaluating a student's answer to a theory question.

Question:
{question_text}

Maximum Marks:
{max_marks}

Student Answer:
{student_answer}

Reference Answer:
{reference_answer or "Not provided"}

Evaluation Criteria:
{evaluation_criteria or "Not provided"}

Evaluate the student's answer fairly.

Consider:
- correctness
- relevance
- completeness
- important concepts
- factual accuracy

Award a mark from 0 to {max_marks} based only on the knowledge demonstrated in the student's answer.

Important grading rules:

1. Do not award marks just because the student repeats the topic name, question keywords, or important terms.
2. If the student only writes the name of the concept/topic without explaining it, award 0 marks.
3. If the student gives only a very short or incomplete definition, award only the marks justified by that content.
4. Do not assume that the student understands concepts that they have not explained.
5. Do not give marks simply because keywords from the reference answer appear in the student's answer.
6. Marks must reflect correctness, relevance, completeness, explanation, and the concepts actually demonstrated.
7. A detailed and correct answer should receive substantially more marks than a keyword-only or one-line answer.
8. For a 5-mark question:
   - 0 marks: no meaningful answer or only the topic/concept name.
   - 1 mark: very limited understanding or a minimally correct statement.
   - 2 marks: basic understanding with some relevant explanation but major concepts missing.
   - 3 marks: reasonably correct explanation but important concepts/details are missing.
   - 4 marks: mostly complete and correct answer with minor omissions.
   - 5 marks: complete, accurate, relevant explanation covering the important expected concepts.
9. Scale these expectations proportionally when the maximum marks are different from 5.
10. Never award several marks for an answer that contains only the question's topic or a few related words.

Return ONLY valid JSON in exactly this format:

{{
    "marks": 0,
    "is_correct": false,
    "feedback": "Concise explanation of the evaluation."
}}

Rules:
- marks must be between 0 and {max_marks}.
- is_correct must be true or false.
- feedback must be concise.
- Do not include markdown.
- Do not include additional fields.
"""


    # ----------------------------------------------------------
    # Send request to Ollama
    # ----------------------------------------------------------

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "think": False,
                "format": "json",
            },
            timeout=180,
        )

        response.raise_for_status()

        data = response.json()


        # ------------------------------------------------------
        # Qwen may return structured output in "thinking"
        # ------------------------------------------------------

        result_text = data.get(
            "response",
            ""
        )


        if not result_text:

            return {
                "marks": 0,
                "max_marks": max_marks,
                "feedback": "AI returned an empty response.",
                "is_correct": None,
                "status": "AI_EMPTY_RESPONSE",
            }


        # ------------------------------------------------------
        # Parse JSON
        # ------------------------------------------------------

        result = json.loads(
            result_text
        )

        print("\n===== THEORY AI RAW RESULT =====")
        print(result_text)
        print("===== THEORY AI PARSED RESULT =====")
        print(result)
        print("=================================\n")


        # ------------------------------------------------------
        # Validate marks
        # ------------------------------------------------------

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


        # ------------------------------------------------------
        # Return evaluation
        # ------------------------------------------------------

        return {
            "marks": marks,
            "max_marks": max_marks,
            "feedback": result.get(
                "feedback",
                "Answer evaluated."
            ),
            "is_correct": result.get(
                "is_correct",
                None
            ),
            "status": "EVALUATED",
        }


    except requests.RequestException as error:

        return {
            "marks": 0,
            "max_marks": max_marks,
            "feedback": (
                f"Could not connect to Ollama: {str(error)}"
            ),
            "is_correct": None,
            "status": "OLLAMA_CONNECTION_ERROR",
        }


    except json.JSONDecodeError as error:

        return {
            "marks": 0,
            "max_marks": max_marks,
            "feedback": (
                f"AI returned invalid JSON: {str(error)}"
            ),
            "is_correct": None,
            "status": "AI_INVALID_JSON",
        }


    except Exception as error:

        return {
            "marks": 0,
            "max_marks": max_marks,
            "feedback": (
                f"AI evaluation failed: {str(error)}"
            ),
            "is_correct": None,
            "status": "AI_ERROR",
        }