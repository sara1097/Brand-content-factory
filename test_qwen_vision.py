import os
import base64
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "qwen/qwen3.6-27b"

IMAGE_PATH = r"C:\Users\Khaled\Desktop\the final project\outputs\images (1).jpg"

with open(IMAGE_PATH, "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """
Analyze this product.

Return ONLY valid JSON.

{
  "name":"",
  "category":"",
  "features":[],
  "visual_analysis":{
    "color":"",
    "design":"",
    "materials":""
  }
}
"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                }
            ]
        }
    ],
    temperature=0.2,
    response_format={"type": "json_object"},
)

print(response.choices[0].message.content)