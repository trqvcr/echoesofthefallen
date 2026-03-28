import base64
from google.genai.types import GenerateImagesConfig

STYLE = (
    "League of Legends cinematic splash art style, painterly digital illustration, "
    "dramatic fantasy lighting, rich saturated colors, highly detailed, "
    "dark fantasy atmosphere, volumetric fog"
)

PORTRAIT_STYLE = (
    "League of Legends splash art style, Riot Games concept art, painterly 2D digital illustration, "
    "artistic oil painting, visible brushwork, stylized fantasy character portrait, "
    "dramatic cinematic rim lighting, deep rich saturated colors, dark fantasy atmosphere, "
    "close-up bust portrait, highly detailed illustrated character, dark moody background"
)


def generate_npc_portrait(client, npc_name: str, npc_description: str) -> str:
    if not client or not npc_description.strip():
        return ""

    styled_prompt = f"{npc_name}: {npc_description.strip()}. {PORTRAIT_STYLE}"
    print(f"[npc-portrait] prompt: {styled_prompt[:120]}...")

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
        print(f"[npc-portrait] generation failed: {e}")

    return ""


def generate_scene_image(client, visual_prompt: str, avatar_description: str = "", npc_description: str = "") -> str:
    if not client or not visual_prompt or visual_prompt.strip().lower() in ("", "[none]"):
        return ""

    scene = visual_prompt.strip().rstrip(".")

    # "Character in scene" pattern gives Imagen the clearest subject + context signal.
    if avatar_description:
        base = f"{avatar_description} in {scene}"
    else:
        base = scene
    if npc_description:
        base += f", alongside {npc_description}"
    styled_prompt = f"{base}. Dark fantasy. {STYLE}"

    print(f"[scene] prompt: {styled_prompt[:120]}...")

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

    styled_prompt = f"{description.strip()}, {PORTRAIT_STYLE}"
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
