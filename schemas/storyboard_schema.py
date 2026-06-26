from pydantic import BaseModel


class StoryboardScene(BaseModel):
    scene_number: int
    goal: str
    visual_description: str
    camera_angle: str
    lighting: str
    motion: str
    duration: int

class Storyboard(BaseModel):
    scenes: list[StoryboardScene]