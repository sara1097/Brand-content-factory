import json

from models.llm import ask_qwen
from schemas.scene_prompt_schema import ScenePrompt, ScenePrompts
from schemas.storyboard_schema import Storyboard
from utils.json_parser import parse_json_response

def generate_scene_prompts(
    storyboard: Storyboard
) -> ScenePrompts:

    prompt = f"""
You are an expert prompt engineer for Wan2.1.

Convert the storyboard into cinematic video prompts.

Return JSON matching this schema:

{json.dumps(ScenePrompts.model_json_schema(), indent=2)}

Storyboard:

{storyboard.model_dump_json(indent=2)}
"""

    response = ask_qwen(prompt)

    raw_prompts = parse_json_response(response)

    # prompts = [
    #     ScenePrompt(**item)
    #     for item in raw_prompts
    # ]
    prompts = ScenePrompts.model_validate(raw_prompts)
    return prompts