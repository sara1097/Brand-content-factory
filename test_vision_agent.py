from agents.vision_agent import extract_visual_information

result = extract_visual_information(
    text_description="Black cotton t-shirt",
    image_path="outputs/images (1).jpg"
)

print(result)