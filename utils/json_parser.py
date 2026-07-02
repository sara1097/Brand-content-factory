import json
import re


def _repair_json(text: str) -> str:
    """
    Try to repair common JSON mistakes produced by LLMs.
    """

    # Remove markdown
    text = text.replace("```json", "")
    text = text.replace("```", "")

    # Remove <think> blocks
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL,
    )

    text = text.strip()

    # Remove trailing commas
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    # Fix missing comma between objects
    text = re.sub(r"}\s*{", "},{", text)

    return text


def parse_json_response(response: str):

    think_match = re.search(
        r"<think>(.*?)</think>",
        response,
        flags=re.DOTALL,
    )

    if think_match:
        print("\n===== Qwen Thinking =====\n")
        print(think_match.group(1).strip())
        print("\n=========================\n")

    cleaned = _repair_json(response)

    print("\n===== Final JSON =====\n")
    print(cleaned)
    print("\n======================\n")

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError as e:

        print("\nJSON Repair Failed\n")
        print(e)

        # محاولة استخراج أول JSON فقط
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start:end + 1])
            except Exception:
                pass

        raise