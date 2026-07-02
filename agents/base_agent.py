from config import DEFAULT_MODEL

from tools.groq_client import (
    call_groq,
    parse_json_response,
)


class BaseAgent:

    def __init__(
        self,
        system_prompt: str,
        settings: dict,
        model: str | None = None,
    ):
        self.system_prompt = system_prompt
        self.settings = settings
        self.model = model or DEFAULT_MODEL

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

        settings = self.settings.copy()
        settings["model"] = self.model

        raw_output = call_groq(
            messages=messages,
            **settings,
        )

        return parse_json_response(
            raw_output,
            retry_messages=messages,
        )