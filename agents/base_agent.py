"""
Base Agent

Reusable base class for all AI agents.
"""

from tools.groq_client import (
    call_groq,
    parse_json_response,
)

class BaseAgent:

    def __init__(
        self,
        system_prompt: str,
        settings: dict,
    ):
        self.system_prompt = system_prompt
        self.settings = settings

    def generate(
        self,
        user_prompt: str,
    ) -> dict:

        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        raw_output = call_groq(
            messages=messages,
            **self.settings,
        )

        return parse_json_response(
            raw_output,
            retry_messages=messages,
        )