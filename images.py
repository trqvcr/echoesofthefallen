import base64
from google.genai.types import GenerateImagesConfig

STYLE = (
    "League of Legends cinematic splash art style, painterly digital illustration, "
    "dramatic fantasy lighting, rich saturated colors, highly detailed, "
    "dark fantasy atmosphere, volumetric fog"
)


def generate_scene_image(client, visual_prompt: str) -> str:
    if not client or not visual_prompt or visual_prompt.strip().lower() in ("", "[none]"):
        return ""

    styled_prompt = f"{visual_prompt.strip()}. {STYLE}"

    try:
        result = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=styled_prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/jpeg",
            ),
        )
        if result.generated_images:
            img_bytes = result.generated_images[0].image.image_bytes
            return f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"
    except Exception as e:
        print(f"Image generation failed: {e}")

    return ""
