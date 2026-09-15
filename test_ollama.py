import requests
import json


OLLAMA_URL = "http://localhost:11434/api/generate"


prompt = """
You are evaluating a student's answer to a theory question.

Question:
What is a primary key in a database?

Maximum Marks:
5

Student Answer:
A primary key is a column that uniquely identifies each record in a table.

Reference Answer:
A primary key uniquely identifies each row in a table. It must contain unique
values and cannot contain NULL values.

Evaluate the student's answer.

Return ONLY valid JSON in exactly this format:

{
    "marks": 0,
    "is_correct": false,
    "feedback": "Concise explanation of the evaluation."
}

Rules:
- marks must be between 0 and 5.
- is_correct must be true or false.
- feedback must be concise.
- Do not include markdown.
- Do not include any additional fields.
"""


payload = {
    "model": "qwen3.5:9b",
    "prompt": prompt,
    "stream": False,
    "format": "json",
}


response = requests.post(
    OLLAMA_URL,
    json=payload,
    timeout=180,
)


print("Status Code:", response.status_code)

data = response.json()

print("\nComplete Ollama Response:")
print(data)


result_text = data.get("response", "")

if not result_text:
    result_text = data.get("thinking", "")


print("\nText Selected For Parsing:")
print(result_text)


print("\nParsed JSON:")

try:

    result = json.loads(result_text)

    print(result)

    print("\nMarks:", result.get("marks"))
    print("Correct:", result.get("is_correct"))
    print("Feedback:", result.get("feedback"))

except json.JSONDecodeError as error:

    print("JSON parsing failed:")
    print(error)