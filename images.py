import base64
from google.genai.types import GenerateImagesConfig

STYLE = (
    "League of Legends cinematic splash art style, painterly digital illustration, "
    "dramatic fantasy lighting, rich saturated colors, highly detailed, "
    "dark fantasy atmosphere, volumetric fog"
)

PORTRAIT_STYLE = (
    "League of Legends character portrait, cinematic splash art, painterly digital illustration, "
    "dramatic rim lighting, rich saturated colors, highly detailed face and armor, "
    "dark fantasy, close-up bust portrait, plain dark background"
)


def generate_scene_image(client, visual_prompt: str, avatar_description: str = "") -> str:
    if not client or not visual_prompt or visual_prompt.strip().lower() in ("", "[none]"):
        return ""

    scene = visual_prompt.strip().rstrip(".")

    # Scene is the primary subject; avatar is a secondary "featuring" clause so
    # Imagen doesn't let the character description hijack the composition.
    if avatar_description:
        styled_prompt = (
            f"{scene}, dark fantasy scene. "
            f"Featuring a character: {avatar_description}. "
            f"{STYLE}"
        )
    else:
        styled_prompt = f"{scene}, dark fantasy scene. {STYLE}"

    print(f"[image] prompt: {styled_prompt[:120]}...")

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
        print(f"[image] generation failed: {e}")

    return ""


def generate_avatar_portrait(client, description: str) -> str:
    if not client or not description.strip():
        return ""

    styled_prompt = f"{description.strip()}. {PORTRAIT_STYLE}"
    print(f"[avatar] prompt: {styled_prompt[:120]}...")

    try:
        result = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=styled_prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/jpeg",
            ),
        )
        if result.generated_images:
            img_bytes = result.generated_images[0].image.image_bytes
            return f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"
    except Exception as e:
        print(f"[avatar] generation failed: {e}")

    return ""
