from pydantic import BaseModel


class ScenePrompt(BaseModel):
    scene_number: int
    prompt: str

class ScenePrompts(BaseModel):
    prompts: list[ScenePrompt]