from groq import Groq
from config import GROQ_API_KEY, MODEL

client = Groq(api_key=GROQ_API_KEY)

def ask_qwen(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
                You are a JSON generator.

                Always return valid JSON.

                Never use markdown.

                Never explain.

                Return only JSON.
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content