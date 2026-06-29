import json
import re


def parse_json_response(response: str):

    # عرض الـ reasoning
    think_match = re.search(
        r"<think>(.*?)</think>",
        response,
        flags=re.DOTALL
    )

    if think_match:
        print("\n===== Qwen Thinking =====\n")
        print(think_match.group(1).strip())
        print("\n=========================\n")

    # حذف التفكير
    cleaned_response = re.sub(
        r"<think>.*?</think>",
        "",
        response,
        flags=re.DOTALL
    )

    # حذف markdown
    cleaned_response = cleaned_response.replace(
        "```json", ""
    )

    cleaned_response = cleaned_response.replace(
        "```", ""
    )

    cleaned_response = cleaned_response.strip()

    # عرض الـ JSON الناتج
    print("\n===== Final JSON =====\n")
    print(cleaned_response)
    print("\n======================\n")

    return json.loads(cleaned_response)