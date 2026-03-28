import base64
from google.genai.types import (
    GenerateImagesConfig,
    GenerateContentConfig,
    EditImageConfig,
    SubjectReferenceImage,
    SubjectReferenceConfig,
    SubjectReferenceType,
    Image,
)

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


def _decode_portrait(b64_str: str) -> bytes | None:
    """Strip data URI prefix and decode base64 to raw bytes. Returns None on failure."""
    if not b64_str:
        return None
    data = b64_str.split(",", 1)[-1] if "," in b64_str else b64_str
    try:
        return base64.b64decode(data)
    except Exception:
        return None


def generate_avatar_visual_prompt(client, description: str, race: str = "", player_class: str = "", gender: str = "") -> str:
    """
    Uses Gemini to expand a player's raw avatar description into a detailed,
    Imagen-optimised visual prompt. The result is stored once and reused for
    every image generated during the game to keep the character consistent.
    """
    if not client or not description.strip():
        return description

    context = ""
    parts = [p for p in [f"Race: {race}" if race else "", f"Class: {player_class}" if player_class else "", f"Gender: {gender}" if gender and gender != "unspecified" else ""] if p]
    if parts:
        context = ". ".join(parts) + ". "

    system_prompt = (
        "You are a character art director for a dark fantasy game in the style of League of Legends cinematic art. "
        "Given a brief player-written character description, expand it into a single, richly detailed visual description "
        "optimised for an AI image generator. "
        "Cover: exact physical features (skin tone, hair colour and style, eye colour, build, height), "
        "clothing and armour (materials, colours, condition, notable details), "
        "any weapons or accessories visibly worn, and one or two character-defining visual details (scars, markings, aura). "
        "Write in plain descriptive prose. No bullet points. No dialogue. No lore. "
        "Keep it under 80 words. Do NOT mention the word 'player'."
    )

    user_msg = f"{context}Player description: {description.strip()}"

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=user_msg,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.4,
                max_output_tokens=150,
            ),
        )
        result = response.text.strip()
        if result:
            print(f"[avatar-prompt] expanded: {result[:120]}...")
            return result
    except Exception as e:
        print(f"[avatar-prompt] expansion failed: {e}")

    return description


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


def generate_scene_image(
    client,
    visual_prompt: str,
    avatar_portrait_b64: str = "",
    npc_portrait_b64: str = "",
) -> str:
    """
    Generate a 16:9 scene image.
    If portrait reference images are provided, uses edit_image with SubjectReferenceImage
    so the character and NPC look consistent with their stored portraits.
    Falls back to standard generate_images if reference-based generation fails.
    """
    if not client or not visual_prompt or visual_prompt.strip().lower() in ("", "[none]"):
        return ""

    scene         = visual_prompt.strip().rstrip(".")
    styled_prompt = f"{scene}. {STYLE}"
    print(f"[scene] prompt: {styled_prompt[:140]}...")

    # Build subject reference list from stored portraits
    references = []
    ref_id     = 1

    avatar_bytes = _decode_portrait(avatar_portrait_b64)
    if avatar_bytes:
        references.append(SubjectReferenceImage(
            reference_id=ref_id,
            reference_image=Image(image_bytes=avatar_bytes, mime_type="image/jpeg"),
            config=SubjectReferenceConfig(subject_type=SubjectReferenceType.SUBJECT_TYPE_PERSON),
        ))
        ref_id += 1

    npc_bytes = _decode_portrait(npc_portrait_b64)
    if npc_bytes:
        references.append(SubjectReferenceImage(
            reference_id=ref_id,
            reference_image=Image(image_bytes=npc_bytes, mime_type="image/jpeg"),
            config=SubjectReferenceConfig(subject_type=SubjectReferenceType.SUBJECT_TYPE_PERSON),
        ))

    # Try reference-driven generation first
    if references:
        try:
            result = client.models.edit_image(
                model="imagen-3.0-capability-001",
                prompt=styled_prompt,
                reference_images=references,
                config=EditImageConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_mime_type="image/jpeg",
                    person_generation="ALLOW_ALL",
                ),
            )
            if result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                return f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"
        except Exception as e:
            print(f"[scene] reference generation failed ({e}), falling back to text-only")

    # Fallback: standard text-to-image
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
        print(f"[scene] fallback generation failed: {e}")

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
