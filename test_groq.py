import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": (
                "Return only the requested output. "
                "Do not explain. "
                "Do not think. "
                "Do not output anything except the final answer."
            )
        },
        {
            "role": "user",
            "content": "Return only: {'test':'ok'}"
        }
    ],
    temperature=0,
    max_tokens=50
)

print(response.choices[0].message.content)