"""
video.py — Veo video + Gemini TTS narration generation for intro cinematic.
"""
import io
import os
import threading
import time
import wave

# ── Video clips ────────────────────────────────────────────────────────────────

INTRO_CLIPS = [
    {
        "path": "intro_video_0.mp4",
        "prompt": (
            "8-bit pixel art animated fantasy scene. Retro SNES/GBA style. "
            "A tall dark stone tower — the Shattered Spire — rises above a misty island at night. "
            "A pixel art king in a gold crown stands at the tower's peak, arms raised toward a sky "
            "crackling with purple void energy and dark tendrils. Stars twinkle. Ash drifts down. "
            "Deep purple and black color palette, glowing crimson accents. "
            "Chunky pixel sprites, limited color palette, smooth looping animation. "
            "Dark fantasy pixel art, 16-color retro aesthetic, animated."
        ),
    },
    {
        "path": "intro_video_1.mp4",
        "prompt": (
            "8-bit pixel art animated fantasy scene. Retro SNES/GBA style. "
            "Night scene: seven dark-robed pixel art cultists stand in a circle around a glowing stone altar. "
            "A crimson void shard pulses on the altar. A pixel king kneels before it. "
            "The sky cracks open — a massive red and black rift tears through the darkness, expanding. "
            "The ground fractures with glowing red cracks. Purple smoke rises. "
            "Deep black and crimson palette, glowing pixel effects. "
            "Chunky pixel sprites, limited color palette, smooth looping animation. "
            "Dark fantasy pixel art, 16-color retro aesthetic, animated."
        ),
    },
    {
        "path": "intro_video_2.mp4",
        "prompt": (
            "8-bit pixel art animated fantasy scene. Retro SNES/GBA style. "
            "A corrupted island wasteland. Ash falls like snow from a dark sky split by a pulsing crimson rift. "
            "Pixel art ruins glow faintly purple. Robed cultist sprites march in the background. "
            "In the foreground, a lone armored pixel hero stands at the edge of a stone settlement wall, "
            "facing the corrupted horizon. The void rift pulses above. "
            "Deep purple, black and ash palette with crimson glow accents. "
            "Chunky pixel sprites, limited color palette, smooth looping animation. "
            "Dark fantasy pixel art, 16-color retro aesthetic, animated."
        ),
    },
]

# ── TTS narration scripts ──────────────────────────────────────────────────────

INTRO_NARRATIONS = [
    {
        "path":  "intro_audio_0.wav",
        "text": (
            "Three hundred years ago, King Aldros Vael ruled the island of Ashenmere "
            "from the Shattered Spire — a tower so tall it pierced the clouds above the Void Wastes. "
            "He was not a cruel king. He was a frightened one. "
            "Terrified of death, he commanded his scholars to find immortality through the void."
        ),
    },
    {
        "path":  "intro_audio_1.wav",
        "text": (
            "On the night of the dark moon, Aldros performed the Rite of Unbinding. "
            "Seven shards. Seven sacrifices. One king who wanted to live forever. "
            "The void answered — but not with the gift he asked for. "
            "Aldros Vael became the Void Entity. Vast. Hungry. And eternal."
        ),
    },
    {
        "path":  "intro_audio_2.wav",
        "text": (
            "The rift never fully closed. For three centuries it has bled void energy "
            "into Ashenmere — corrupting the land, twisting its creatures. "
            "A cult called The Awakened seeks to free him. "
            "They are close to finishing what Aldros started. "
            "Your house has always stood against the darkness. "
            "Now, it falls to you."
        ),
    },
]

# ── Intro still images (replace videos) ───────────────────────────────────────

INTRO_IMAGES = [
    # ── Clip 0: The King Who Reached Too Far ──────────────────────────────────
    {
        "path": "intro_image_0.jpg",
        "clip": 0,
        "prompt": (
            "16-bit pixel art dark fantasy landscape, wide cinematic 16:9. "
            "A vast night sky crackles with swirling purple void energy above a jagged dark island coast. "
            "A towering stone spire — the Shattered Spire — dominates the center, its peak wreathed in glowing crimson and violet tendrils. "
            "At the summit, a tiny crowned king figure reaches upward. Ash drifts like snow. "
            "Stars twinkle. Deep blacks, muted purples, and crimson glows. "
            "SNES/GBA retro pixel art style, chunky sprites, limited palette, no antialiasing."
        ),
    },
    {
        "path": "intro_image_1.jpg",
        "clip": 0,
        "prompt": (
            "16-bit pixel art dark fantasy interior, wide cinematic 16:9. "
            "A candlelit stone scriptorium deep inside a dark tower. Robed pixel art scholars hunch over enormous "
            "open tomes on stone desks, scrawling void runes by candlelight. Shelves of crumbling books line the walls. "
            "A crowned king pixel sprite paces behind them, face etched with fear, clutching a skull-carved scepter. "
            "Candles cast long purple and amber shadows. Dust motes drift in the air. "
            "SNES/GBA retro pixel art style, chunky sprites, warm candlelight against deep purple shadows."
        ),
    },
    # ── Clip 1: The Night of the Shattering ───────────────────────────────────
    {
        "path": "intro_image_2.jpg",
        "clip": 1,
        "prompt": (
            "16-bit pixel art dark fantasy scene, wide cinematic 16:9. "
            "Night. Seven black-robed cultist pixel sprites stand in a ritual circle on cracked stone ground. "
            "At the center, a jagged crimson void shard floats above an altar, pulsing with red light. "
            "A crowned king kneels before it. The sky above tears open — a massive obsidian and crimson rift, "
            "jagged edges glowing, red energy pouring down. Glowing ground cracks radiate outward. "
            "SNES/GBA retro pixel art style, chunky sprites, limited palette, dramatic backlighting."
        ),
    },
    {
        "path": "intro_image_3.jpg",
        "clip": 1,
        "prompt": (
            "16-bit pixel art dark fantasy close-up, wide cinematic 16:9. "
            "Extreme close-up on a jagged crimson void shard hovering above a carved stone altar. "
            "It pulses with malevolent red and black energy, dark runes glowing on the altar base. "
            "Two gauntleted royal hands reach into frame from below, trembling, fingertips nearly touching the shard. "
            "The air around it shimmers and warps. Black void tendrils curl outward. "
            "SNES/GBA retro pixel art style, high contrast crimson glow, dark vignette, dramatic tension."
        ),
    },
    {
        "path": "intro_image_4.jpg",
        "clip": 1,
        "prompt": (
            "16-bit pixel art dark fantasy transformation scene, wide cinematic 16:9. "
            "King Aldros pixel sprite stands at the center of the ritual circle, arms flung wide, crown floating above his head. "
            "His body fractures and dissolves — pixel chunks breaking apart into streams of black void energy that spiral upward "
            "into the rift above. His eyes blaze solid red. The cultists around him recoil in horror. "
            "The sky is torn open with blinding crimson light. "
            "SNES/GBA retro pixel art style, explosive light effects, chunky sprites disintegrating."
        ),
    },
    # ── Clip 2: An Heir Rises ─────────────────────────────────────────────────
    {
        "path": "intro_image_5.jpg",
        "clip": 2,
        "prompt": (
            "16-bit pixel art dark fantasy landscape, wide cinematic 16:9. "
            "A ruined wasteland under an ashen sky. A massive crimson void rift tears across the upper sky, "
            "bleeding red light down onto crumbling stone ruins below. "
            "Pixel art ash falls like snow. Robed cultist sprites march toward the rift in the midground. "
            "In the foreground, a lone armored knight pixel sprite stands at a stone wall, "
            "gazing toward the corrupted horizon, sword at their side. "
            "SNES/GBA retro pixel art style, chunky sprites, muted ash palette with crimson glow accents."
        ),
    },
    {
        "path": "intro_image_6.jpg",
        "clip": 2,
        "prompt": (
            "16-bit pixel art dark fantasy interior, wide cinematic 16:9. "
            "A torch-lit ancestral stone hall at night. A lone armored pixel sprite sits at a heavy wooden table, "
            "sharpening a sword by torchlight. Maps and wax-sealed letters are spread across the table. "
            "A faded family crest — a tower beneath a broken star — hangs on the stone wall behind them. "
            "A narrow arrow-slit window shows ash drifting past outside against a red-tinged sky. "
            "SNES/GBA retro pixel art style, warm orange torchlight, heavy shadows, muted earth palette."
        ),
    },
]

# ── State tracking ─────────────────────────────────────────────────────────────

_clip_states  = [{"generating": False, "error": None} for _ in INTRO_CLIPS]
_audio_states = [{"generating": False, "error": None} for _ in INTRO_NARRATIONS]
_image_states = [{"generating": False, "error": None} for _ in INTRO_IMAGES]

# Map clip index → list of image indices for that clip
CLIP_IMAGE_MAP = {}
for _i, _img in enumerate(INTRO_IMAGES):
    _c = _img.get("clip", 0)
    CLIP_IMAGE_MAP.setdefault(_c, []).append(_i)

# Legacy compat
INTRO_VIDEO_PATH = INTRO_CLIPS[0]["path"]


# ── Status helpers ─────────────────────────────────────────────────────────────

def clip_status(idx: int) -> str:
    clip = INTRO_CLIPS[idx]
    if os.path.exists(clip["path"]):
        return "ready"
    state = _clip_states[idx]
    if state["generating"]: return "generating"
    if state["error"]:      return "error"
    return "none"


def audio_status(idx: int) -> str:
    narration = INTRO_NARRATIONS[idx]
    if os.path.exists(narration["path"]):
        return "ready"
    state = _audio_states[idx]
    if state["generating"]: return "generating"
    if state["error"]:      return "error"
    return "none"


def image_status(idx: int) -> str:
    img = INTRO_IMAGES[idx]
    if os.path.exists(img["path"]):
        return "ready"
    state = _image_states[idx]
    if state["generating"]: return "generating"
    if state["error"]:      return "error"
    return "none"


def intro_video_status() -> str:
    statuses = [clip_status(i) for i in range(len(INTRO_CLIPS))]
    if all(s == "ready" for s in statuses):
        return "ready"
    if any(s in ("generating", "ready") for s in statuses):
        return "generating"
    return "none"


# ── Video generation ───────────────────────────────────────────────────────────

def _run_clip_generation(client, idx: int):
    state = _clip_states[idx]
    clip  = INTRO_CLIPS[idx]
    try:
        from google.genai.types import GenerateVideosConfig
        print(f"[veo] starting clip {idx + 1} generation...")
        operation = client.models.generate_videos(
            model="veo-3.0-generate-001",
            prompt=clip["prompt"],
            config=GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=8,
            ),
        )
        print(f"[veo] polling clip {idx + 1}...")
        while not operation.done:
            time.sleep(8)
            operation = client.operations.get(operation)

        video_bytes = operation.response.generated_videos[0].video.video_bytes
        with open(clip["path"], "wb") as f:
            f.write(video_bytes)
        print(f"[veo] clip {idx + 1} saved to {clip['path']}")
    except Exception as e:
        state["error"] = str(e)
        print(f"[veo] clip {idx + 1} failed: {e}")
    finally:
        state["generating"] = False


# ── TTS narration generation ───────────────────────────────────────────────────

def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)      # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def _run_tts_generation(client, idx: int):
    state     = _audio_states[idx]
    narration = INTRO_NARRATIONS[idx]
    try:
        from google.genai.types import GenerateContentConfig, SpeechConfig, VoiceConfig, PrebuiltVoiceConfig
        import base64

        print(f"[tts] generating narration {idx + 1}...")
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=narration["text"],
            config=GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=SpeechConfig(
                    voice_config=VoiceConfig(
                        prebuilt_voice_config=PrebuiltVoiceConfig(voice_name="Kore")
                    )
                ),
            ),
        )

        raw = response.candidates[0].content.parts[0].inline_data.data
        # SDK may return bytes or a base64 string depending on version
        if isinstance(raw, str):
            raw = base64.b64decode(raw)

        wav_bytes = _pcm_to_wav(raw)
        with open(narration["path"], "wb") as f:
            f.write(wav_bytes)
        print(f"[tts] narration {idx + 1} saved to {narration['path']}")
    except Exception as e:
        state["error"] = str(e)
        print(f"[tts] narration {idx + 1} failed: {e}")
    finally:
        state["generating"] = False


# ── Inline TTS (one-shot, returns base64 WAV) ─────────────────────────────────

def generate_tts_audio(client, text: str) -> str:
    """
    Generate TTS for arbitrary text and return a base64-encoded WAV string.
    Returns empty string on failure.
    """
    if not client or not text.strip():
        return ""
    try:
        from google.genai.types import GenerateContentConfig, SpeechConfig, VoiceConfig, PrebuiltVoiceConfig
        import base64 as _b64

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=SpeechConfig(
                    voice_config=VoiceConfig(
                        prebuilt_voice_config=PrebuiltVoiceConfig(voice_name="Kore")
                    )
                ),
            ),
        )
        raw = response.candidates[0].content.parts[0].inline_data.data
        if isinstance(raw, str):
            raw = _b64.b64decode(raw)
        wav_bytes = _pcm_to_wav(raw)
        return _b64.b64encode(wav_bytes).decode()
    except Exception as e:
        print(f"[tts] inline generation failed: {e}")
        return ""


# ── Still image generation ────────────────────────────────────────────────────

def _run_image_generation(client, idx: int):
    state = _image_states[idx]
    img   = INTRO_IMAGES[idx]
    try:
        from google.genai.types import GenerateImagesConfig
        import base64 as _b64
        print(f"[imagen] generating intro image {idx + 1}...")
        result = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=img["prompt"],
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/jpeg",
            ),
        )
        if result.generated_images:
            img_bytes = result.generated_images[0].image.image_bytes
            with open(img["path"], "wb") as f:
                f.write(img_bytes)
            print(f"[imagen] intro image {idx + 1} saved to {img['path']}")
        else:
            raise RuntimeError("No images returned")
    except Exception as e:
        state["error"] = str(e)
        print(f"[imagen] intro image {idx + 1} failed: {e}")
    finally:
        state["generating"] = False


# ── Kick off all generation ────────────────────────────────────────────────────

def start_intro_generation(client) -> str:
    """
    Kicks off background image + TTS generation for anything not yet done.
    Returns overall status string.
    """
    if not client:
        return "no_client"

    for idx, img in enumerate(INTRO_IMAGES):
        if not os.path.exists(img["path"]) and not _image_states[idx]["generating"]:
            _image_states[idx]["generating"] = True
            _image_states[idx]["error"]      = None
            threading.Thread(target=_run_image_generation, args=(client, idx), daemon=True).start()

    for idx, narration in enumerate(INTRO_NARRATIONS):
        if not os.path.exists(narration["path"]) and not _audio_states[idx]["generating"]:
            _audio_states[idx]["generating"] = True
            _audio_states[idx]["error"]      = None
            threading.Thread(target=_run_tts_generation, args=(client, idx), daemon=True).start()

    return intro_video_status()
