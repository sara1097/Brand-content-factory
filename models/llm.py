from config import MODEL
from tools.groq_client import create_chat_completion


def ask_qwen(
    prompt: str,
    model: str | None = None,
    max_completion_tokens: int = 4000,
) -> str:
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
        # Groq's TPM limit counts prompt tokens PLUS this reservation,
        # so callers with long prompts should pass a small budget here.
        max_completion_tokens=max_completion_tokens,
    )

    print("\n========== GROQ USAGE ==========")
    print(response.usage)
    print("================================\n")

    return response.choices[0].message.content