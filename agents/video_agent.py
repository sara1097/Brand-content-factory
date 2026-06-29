from agents.storyboard_agent import generate_storyboard
from agents.prompt_agent import generate_scene_prompts
from models.wan_generator import generate_video
from utils.moviepy_builder import compose_video
from schemas.marketing_schema import MarketingInput
def build_marketing_input(
    marketing: dict,
    content: dict,
) -> MarketingInput:

    return MarketingInput(

        campaign_context={

            "campaign_goal":
                marketing.get(
                    "data_sources",
                    {}
                ).get(
                    "primary_goal",
                    ""
                ),

            "campaign_name":
                marketing.get(
                    "campaign_strategy",
                    {}
                ).get(
                    "attributes",
                    {}
                ).get(
                    "campaign_name",
                    "Marketing Campaign"
                ),

        },

        target_persona={

            "target_audience":
                marketing.get(
                    "stp_analysis",
                    {}
                ).get(
                    "attributes",
                    {}
                ).get(
                    "target_audience",
                    []
                ),

            "pain_points":
                marketing.get(
                    "stp_analysis",
                    {}
                ).get(
                    "attributes",
                    {}
                ).get(
                    "pain_points",
                    []
                ),

            "motivations":
                marketing.get(
                    "stp_analysis",
                    {}
                ).get(
                    "attributes",
                    {}
                ).get(
                    "customer_motivations",
                    []
                ),

        },

        platform_context={

            "social_platforms":
                marketing.get(
                    "channel_strategy",
                    {}
                ).get(
                    "attributes",
                    {}
                ).get(
                    "social_platforms",
                    []
                ),

        },

        content_input=content,

        creative_constraints={

            "video_style": "cinematic",

            "video_duration": 20,

            "language": "English"

        }

    )

def generate_video_assets(marketing: dict, content: dict):
    marketing_input = build_marketing_input(marketing, content)
    
    storyboard = generate_storyboard(marketing_input)
    scene_prompts = generate_scene_prompts(storyboard)

    video_paths = []
    
    for scene in scene_prompts.prompts:
        path = generate_video(
            scene.prompt,
            f"outputs/video_{scene.scene_number}.mp4"
        )
        video_paths.append(path)

    final_video = compose_video(video_paths)

    return {
        "storyboard": storyboard.model_dump(),
        "scene_prompts": scene_prompts.model_dump(),
        "video_paths": video_paths,
        "final_video": final_video,
    }