import json

from models.llm import ask_qwen
from schemas.marketing_schema import MarketingInput
from schemas.storyboard_schema import Storyboard, StoryboardScene
from utils.json_parser import parse_json_response

def generate_storyboard(marketing_data: MarketingInput):

    prompt = f"""
You are a cinematic advertisement director.

Generate 4 scenes.

Return ONLY a JSON array.

Do not explain anything.

Do not use markdown.

Do not wrap the answer with ```json.

Marketing information:

{marketing_data.model_dump_json(indent=2)}

Format:

[
{{
"scene_number":1,
"goal":"",
"visual_description":"",
"camera_angle":"",
"lighting":"",
"motion":"",
"duration":5
}}
]
"""

    response = ask_qwen(prompt)
    print(response)
    raw_scenes = parse_json_response(response)

    scenes = [
        StoryboardScene(**scene)
        for scene in raw_scenes
    ]
    
    return Storyboard(scenes=scenes)