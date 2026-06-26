from schemas.marketing_schema import MarketingInput
from agents.storyboard_agent import generate_storyboard
from agents.prompt_agent import generate_scene_prompts


# sample_input = MarketingInput(
#     campaign_context={},
#     target_persona={},
#     platform_context={},
#     content_input={},
#     creative_constraints={}
# )
# sample_input = MarketingInput(
#     campaign_context={
#         "campaign_goal": "Increase subscriptions"
#     },

#     target_persona={
#         "age_range": "20-35",
#         "interests": [
#             "fitness",
#             "healthy lifestyle"
#         ]
#     },

#     platform_context={
#         "platform": "Instagram Reels"
#     },

#     content_input={
#         "post_idea": "Busy people can still stay fit",
#         "hook": "No time for the gym?",
#         "caption": "Transform your health in 15 minutes a day.",
#         "hashtags": [
#             "#fitness",
#             "#health"
#         ],
#         "cta": "Download our app today"
#     },

#     creative_constraints={
#         "video_duration": 20,
#         "style": "cinematic"
#     }
# )

sample_input = MarketingInput(
    campaign_context={
        "campaign_goal": "Drive product awareness and brand association with athletic performance"
    },

    target_persona={
        "age_range": "20-35",
        "interests": [
            "fitness",
            "urban running",
            "athleisure style"
        ]
    },

    platform_context={
        "platform": "Instagram Reels"
    },

    content_input={
        "post_idea": "The comfort and energy return of Nona sneakers",
        "hook": "Step into your peak performance.",
        "caption": "Engineered for movement. Designed for you. Experience the new Nona sneakers.",
        "hashtags": [
            "#NonaShoes",
            "#MoveWithNona",
            "#PeakPerformance"
        ],
        "cta": "Shop the Nona collection online"
    },

    creative_constraints={
        "video_duration": 10,
        "style": "cinematic, high-energy yet smooth, focus on product details"
    }
)

storyboard = generate_storyboard(sample_input)

print("\nStoryboard:")
print(storyboard.model_dump_json(indent=2))

scene_prompts = generate_scene_prompts(storyboard)

print("\nScene Prompts:")
print(scene_prompts.model_dump_json(indent=2))