MUSIC_PROMPTS = {
    "combat": (
        "Intense dark fantasy battle music. Urgent driving rhythm with pounding war drums. "
        "Menacing strings and brass stabs. Orchestral, high tension, relentless momentum."
    ),
    "ashen_ruins": (
        "Dark ambient music for exploring ancient ruins. Haunting desolate atmosphere. "
        "Low drones, distant echoes, sparse piano notes, minor key strings. Eerie and foreboding."
    ),
    "saltmarsh": (
        "Melancholic medieval town ambience. Gentle lute plucking, soft strings, quiet warmth. "
        "Bittersweet, calm, a weary traveller's respite from darkness."
    ),
    "void_wastes": (
        "Ominous ambient soundscape for a void-corrupted wasteland. Deep resonant drones, "
        "alien textures, unsettling silence broken by distant spectral howls. Dark and vast."
    ),
    "default": (
        "Dark ambient fantasy music. Mysterious and atmospheric. "
        "Brooding strings, distant horn call, minor key, slow tempo."
    ),
}


def get_music_context(location_key: str, in_combat: bool) -> str:
    if in_combat:
        return "combat"
    loc = location_key.lower() if location_key else ""
    if any(x in loc for x in ("ruin", "keep", "library", "courtyard", "bridge")):
        return "ashen_ruins"
    if any(x in loc for x in ("saltmarsh", "flagon", "market", "gate")):
        return "saltmarsh"
    if any(x in loc for x in ("void", "waste")):
        return "void_wastes"
    return "default"


def generate_ambient_music(client, location_key: str, in_combat: bool) -> tuple[str, str]:
    """Generate ambient music for the current game context.
    Returns (data_url, music_context). data_url is empty string on failure."""
    context = get_music_context(location_key, in_combat)
    if not client:
        return "", context

    prompt = MUSIC_PROMPTS[context]
    print(f"[music] generating for context: {context}")

    try:
        import base64
        from google.genai import types
        response = client.models.generate_content(
            model="lyria-3-clip-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
            ),
        )
        parts = response.candidates[0].content.parts
        print(f"[music] response has {len(parts)} part(s)")
        for part in parts:
            if part.inline_data is not None:
                audio_bytes = part.inline_data.data
                mime_type   = part.inline_data.mime_type or "audio/mp3"
                print(f"[music] got audio: {mime_type}, {len(audio_bytes)} bytes")
                audio_b64 = base64.b64encode(audio_bytes).decode()
                return f"data:{mime_type};base64,{audio_b64}", context
        print(f"[music] no audio part found; parts: {[(p.text[:40] if p.text else 'inline_data') for p in parts]}")
        return "", context
    except Exception as e:
        print(f"[music] generation failed: {type(e).__name__}: {e}")
        return "", context
