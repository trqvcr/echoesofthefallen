"""
video.py — Veo video + Gemini TTS narration generation for intro cinematic and in-game cutscenes.
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

_CINEMATIC = (
    "League of Legends cinematic splash art style, painterly digital illustration, "
    "dramatic fantasy lighting, rich saturated colors, highly detailed, "
    "dark fantasy atmosphere, volumetric fog, wide cinematic 16:9 composition"
)

INTRO_IMAGES = [
    # ── Clip 0: The King Who Reached Too Far ──────────────────────────────────
    {
        "path": "intro_image_0.jpg",
        "clip": 0,
        "prompt": (
            "Dark fantasy cinematic landscape. A colossal obsidian spire — the Shattered Spire — "
            "erupts from a mist-shrouded island at night. Its peak crackles with swirling violet and crimson void energy. "
            "A lone crowned king stands silhouetted at the very summit, arms raised toward a sky torn with dark tendrils. "
            "Ash drifts like snow across a deep purple and black sky. Distant stars bleed into the void. "
            "Dramatic low-angle shot, volumetric god-rays of dark energy, ominous grandeur. "
            + _CINEMATIC
        ),
    },
    {
        "path": "intro_image_1.jpg",
        "clip": 0,
        "prompt": (
            "Dark fantasy cinematic interior. A vast candlelit stone scriptorium inside a dark tower. "
            "Hunched scholars in dark robes pore over enormous crumbling tomes on heavy stone desks, "
            "quills scratching void runes by candlelight. Floor-to-ceiling shelves overflow with decaying books. "
            "A crowned king in ornate gold armor paces behind them, face gaunt with fear, a skull-carved scepter in hand. "
            "Amber candlelight battles deep purple shadow. Dust motes drift through shafts of dim light. "
            "Cinematic wide shot, warm chiaroscuro lighting, oppressive dread. "
            + _CINEMATIC
        ),
    },
    # ── Clip 1: The Night of the Shattering ───────────────────────────────────
    {
        "path": "intro_image_2.jpg",
        "clip": 1,
        "prompt": (
            "Dark fantasy cinematic ritual scene. Night. Seven black-robed cultists stand in a perfect circle "
            "on cracked ancient stone ground, arms raised in dark supplication. "
            "At the circle's center a jagged crimson void shard hovers above a carved altar, pulsing with malevolent red light. "
            "A crowned king kneels before it, reaching upward. The sky above splits open — "
            "a massive obsidian and crimson rift tears through the heavens, pouring down waves of dark energy. "
            "Ground cracks glow red. Smoke and ash churn. "
            "Dramatic overhead cinematic angle, hellish backlighting, catastrophic atmosphere. "
            + _CINEMATIC
        ),
    },
    {
        "path": "intro_image_3.jpg",
        "clip": 1,
        "prompt": (
            "Dark fantasy cinematic close-up. An extreme close-up of a jagged crimson void shard "
            "hovering above a carved obsidian altar, radiating malevolent red and black energy. "
            "Ancient void runes on the altar base pulse with dim light. "
            "Two trembling gauntleted royal hands reach into frame from below, fingertips inches from the shard. "
            "The air warps and tears around it. Black tendrils curl outward like fingers. "
            "Macro cinematic shot, intense crimson and black contrast, heavy dramatic vignette. "
            + _CINEMATIC
        ),
    },
    {
        "path": "intro_image_4.jpg",
        "clip": 1,
        "prompt": (
            "Dark fantasy cinematic transformation. King Aldros stands at the ritual circle's center, "
            "arms flung wide, crown floating above his head in the vortex. "
            "His body dissolves — flesh unraveling into streams of black void energy that spiral upward into the rift. "
            "His eyes burn solid crimson. The cultists around him recoil in terror. "
            "The sky blazes with blinding red-white light as the void consumes him entirely. "
            "Epic wide cinematic shot, explosive light blooms, catastrophic transformation energy. "
            + _CINEMATIC
        ),
    },
    # ── Clip 2: An Heir Rises ─────────────────────────────────────────────────
    {
        "path": "intro_image_5.jpg",
        "clip": 2,
        "prompt": (
            "Dark fantasy cinematic wasteland. A vast corrupted island under a churning ashen sky. "
            "A massive crimson void rift tears across the upper atmosphere, bleeding red light onto crumbling stone ruins below. "
            "Fine ash falls like snow. Black-robed cultists march in formation toward the rift in the midground. "
            "In the foreground, a lone armored knight stands at a crumbling stone wall, "
            "gazing toward the corrupted horizon, sword at their side. "
            "Cinematic wide establishing shot, ashen muted palette with crimson glow accents, desolate grandeur. "
            + _CINEMATIC
        ),
    },
    {
        "path": "intro_image_6.jpg",
        "clip": 2,
        "prompt": (
            "Dark fantasy cinematic interior. A torch-lit ancestral stone hall at night. "
            "A lone armored figure sits at a heavy oak table, sharpening a sword by torchlight. "
            "Maps and wax-sealed letters are spread across the table. "
            "A weathered stone wall bears a carved family crest — a tower beneath a broken star. "
            "A narrow arrow-slit window reveals ash drifting past a red-tinged night sky outside. "
            "Intimate cinematic composition, warm amber torchlight against heavy shadow, quiet resolve. "
            + _CINEMATIC
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
    if os.path.exists(clip["path"]) and os.path.getsize(clip["path"]) > 0:
        return "ready"
    state = _clip_states[idx]
    if state["generating"]: return "generating"
    if state["error"]:      return "error"
    return "none"


def audio_status(idx: int) -> str:
    narration = INTRO_NARRATIONS[idx]
    if os.path.exists(narration["path"]) and os.path.getsize(narration["path"]) > 0:
        return "ready"
    state = _audio_states[idx]
    if state["generating"]: return "generating"
    if state["error"]:      return "error"
    return "none"


def image_status(idx: int) -> str:
    img = INTRO_IMAGES[idx]
    if os.path.exists(img["path"]) and os.path.getsize(img["path"]) > 0:
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


# ── In-game cutscenes ──────────────────────────────────────────────────────────

CUTSCENE_CLIPS = {
    # location entry cutscenes
    "ruined_keep": {
        "path": "cutscene_ruined_keep.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. A lone armored warrior pushes open massive rusted iron gates "
            "into a crumbling fortress keep. Inside: collapsed stone halls choked with ash, "
            "void energy crackling faintly along cracked pillars, ravens scattering into a grey sky. "
            "The camera drifts forward through the gate into shadow. "
            "Cinematic dark fantasy, dramatic volumetric lighting, League of Legends cutscene quality."
        ),
    },
    "throne_vault": {
        "path": "cutscene_throne_vault.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. A vast underground throne room revealed as a stone door grinds open. "
            "A colossal obsidian throne sits at the far end, surrounded by the skeletal remains of ancient guards "
            "still standing at their posts. Void energy pulses faintly in the cracks of the floor. "
            "The camera glides slowly toward the throne through drifting ash and cold blue light. "
            "Cinematic dark fantasy, eerie and grand, League of Legends cutscene quality."
        ),
    },
    "sunken_library": {
        "path": "cutscene_sunken_library.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. A vast library half-submerged in dark water. "
            "Towering shelves of ancient tomes stretch upward into a vaulted stone ceiling. "
            "Candles burn impossibly on floating debris. Void-touched pages drift through the air like moths. "
            "The camera descends a mossy staircase into the flooded hall, water rippling with strange light. "
            "Cinematic dark fantasy, atmospheric and mysterious, League of Legends cutscene quality."
        ),
    },
    "ritual_chamber": {
        "path": "cutscene_ritual_chamber.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. A hidden ritual chamber unearthed. "
            "A perfect circle of black stone altars surrounds a cracked obsidian shard at the center — "
            "pulsing with deep crimson void energy. Ancient runes carved into the floor glow and dim. "
            "The camera descends slowly from above, rotating around the shard. "
            "Oppressive silence. Ash drifts downward through a crack in the vaulted ceiling. "
            "Cinematic dark fantasy, foreboding and epic, League of Legends cutscene quality."
        ),
    },
    "void_wastes_edge": {
        "path": "cutscene_void_wastes_edge.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. A warrior reaches the edge of the void wastes — "
            "a devastated landscape of cracked black earth stretching to a massive crimson rift in the sky. "
            "The air shimmers with dark energy. Dead twisted trees line the horizon. "
            "The camera pulls back slowly as the warrior stands small against the vast corrupted sky. "
            "Cinematic dark fantasy, massive scale, ominous and awe-inspiring, League of Legends cutscene quality."
        ),
    },
    "saltmarsh_gate": {
        "path": "cutscene_saltmarsh_gate.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. A survivor's settlement emerges from the ash — "
            "rough stone walls lit by torchlight, a heavy iron gate swinging open. "
            "Inside: people huddle around fires, merchants call out in hoarse voices, "
            "guards with hollow eyes patrol the walls. "
            "The camera moves through the gate into the crowded, desperate settlement. "
            "Cinematic dark fantasy, gritty and human, League of Legends cutscene quality."
        ),
    },
    # story moment cutscenes
    "act_2_begins": {
        "path": "cutscene_act2.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. The corruption spreads. "
            "A massive void tendril tears through the sky above the ruined island, "
            "crackling with dark energy, splitting storm clouds apart. "
            "Below, the land itself darkens — ash deepens, the void rift grows. "
            "The camera tilts upward slowly from ground level toward the expanding rift. "
            "Dread and inevitability. Cinematic dark fantasy, League of Legends cutscene quality."
        ),
    },
    "act_3_begins": {
        "path": "cutscene_act3.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. The final hour. "
            "The void rift has split the sky in two — a colossal tear from horizon to horizon, "
            "pouring dark energy down onto the dying island. "
            "A lone figure stands on the highest ruined parapet, sword drawn, facing the sky. "
            "Wind howls. Ash swirls. The world is ending. "
            "The camera orbits the figure slowly. Cinematic dark fantasy, epic and final, League of Legends cutscene quality."
        ),
    },
}

_cutscene_states = {key: {"generating": False, "error": None} for key in CUTSCENE_CLIPS}


def cutscene_status(key: str) -> str:
    """Returns 'ready', 'generating', 'error', or 'none'."""
    clip = CUTSCENE_CLIPS.get(key)
    if not clip:
        return "none"
    if os.path.exists(clip["path"]) and os.path.getsize(clip["path"]) > 0:
        return "ready"
    state = _cutscene_states[key]
    if state["generating"]:
        return "generating"
    if state["error"]:
        return "error"
    return "none"


def get_cutscene_url(key: str) -> str:
    """Returns the server URL for a ready cutscene, or empty string."""
    if cutscene_status(key) == "ready":
        return f"/cutscene/{key}"
    return ""


def _run_cutscene_generation(client, key: str):
    state = _cutscene_states[key]
    clip  = CUTSCENE_CLIPS[key]
    try:
        from google.genai.types import GenerateVideosConfig
        print(f"[veo] starting cutscene '{key}' generation...")
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=clip["prompt"],
            config=GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=8,
            ),
        )
        print(f"[veo] polling cutscene '{key}'...")
        while not operation.done:
            time.sleep(8)
            operation = client.operations.get(operation)

        video_bytes = operation.response.generated_videos[0].video.video_bytes
        with open(clip["path"], "wb") as f:
            f.write(video_bytes)
        print(f"[veo] cutscene '{key}' saved to {clip['path']}")
    except Exception as e:
        state["error"] = str(e)
        print(f"[veo] cutscene '{key}' failed: {e}")
    finally:
        state["generating"] = False


def start_cutscene_generation(client):
    """Kick off background generation for all cutscenes not yet on disk."""
    if not client:
        return
    for key, clip in CUTSCENE_CLIPS.items():
        if not os.path.exists(clip["path"]) and not _cutscene_states[key]["generating"]:
            _cutscene_states[key]["generating"] = True
            _cutscene_states[key]["error"]      = None
            t = threading.Thread(target=_run_cutscene_generation, args=(client, key), daemon=True)
            t.start()
