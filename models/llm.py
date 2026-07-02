from config import MODEL
from tools.groq_client import create_chat_completion


def ask_qwen(prompt: str, model: str | None = None) -> str:
    response = create_chat_completion(
        model=model or MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a JSON generator.

Always return ONLY one valid JSON object.

Do not use markdown.

Do not explain anything.

Never include <think> tags.

Never include reasoning.

Return valid JSON only.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_completion_tokens=4000,
    )

    print("\n========== GROQ USAGE ==========")
    print(response.usage)
    print("================================\n")

    return response.choices[0].message.content