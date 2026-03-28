"""
video.py — Veo video generation for intro cinematic (3 lore clips).
"""
import os
import threading
import time

INTRO_CLIPS = [
    {
        "path": "intro_video_1.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. Three centuries in the past. "
            "A colossal dark tower — the Shattered Spire — pierces storm clouds above a misty island coast. "
            "At its peak, a robed king with a golden crown reaches toward a sky laced with void energy — "
            "dark tendrils spiraling through dying stars. His face is desperate, obsessed. "
            "The island below is ancient and scarred. Ash drifts on the wind. "
            "Cinematic dark fantasy, dramatic volumetric lighting, deep shadows, League of Legends cutscene quality."
        ),
    },
    {
        "path": "intro_video_2.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. The night of the dark moon. "
            "Seven black-robed cultists encircle a cracked stone altar in a desolate ash wasteland. "
            "A void shard at the altar's center pulses with crimson energy. A king kneels before it. "
            "The ritual ignites — dark smoke rises, the earth fractures, "
            "a massive rift tears open in the sky: obsidian and crimson, pulsing with dark power. "
            "The king's body dissolves into void light as the island shakes and splits. "
            "Dramatic volumetric lighting, dark fantasy, cinematic quality."
        ),
    },
    {
        "path": "intro_video_3.mp4",
        "prompt": (
            "Epic dark fantasy cinematic. Present day. A dying island consumed by void corruption. "
            "Ash falls like snow from a sky split by a massive crimson void rift. "
            "Ruins glow with cursed dark energy. Robed cultists march through the wasteland toward the rift. "
            "At the coast, a lone armored figure stands at the edge of a walled stone settlement, "
            "gazing toward the corrupted interior. The void rift pulses above. Patient as the dark between stars. "
            "Cinematic dark fantasy, dramatic lighting, ominous and epic, League of Legends quality."
        ),
    },
]

# Per-clip state
_clip_states = [{"generating": False, "error": None} for _ in INTRO_CLIPS]

# Legacy compat
INTRO_VIDEO_PATH = INTRO_CLIPS[0]["path"]


def clip_status(idx: int) -> str:
    """Returns 'ready', 'generating', 'error', or 'none' for clip at idx."""
    clip = INTRO_CLIPS[idx]
    if os.path.exists(clip["path"]):
        return "ready"
    state = _clip_states[idx]
    if state["generating"]:
        return "generating"
    if state["error"]:
        return "error"
    return "none"


def intro_video_status() -> str:
    """Overall status: 'ready' if all clips exist, else 'generating' or 'none'."""
    statuses = [clip_status(i) for i in range(len(INTRO_CLIPS))]
    if all(s == "ready" for s in statuses):
        return "ready"
    if any(s in ("generating", "ready") for s in statuses):
        return "generating"
    return "none"


def _run_clip_generation(client, idx: int):
    state = _clip_states[idx]
    clip  = INTRO_CLIPS[idx]
    try:
        from google.genai.types import GenerateVideosConfig
        print(f"[veo] starting clip {idx + 1} generation...")
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
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


def start_intro_generation(client) -> str:
    """
    Kicks off background Veo generation for all clips not yet done.
    Returns overall status string.
    """
    if not client:
        return "no_client"

    for idx, clip in enumerate(INTRO_CLIPS):
        if not os.path.exists(clip["path"]) and not _clip_states[idx]["generating"]:
            _clip_states[idx]["generating"] = True
            _clip_states[idx]["error"]      = None
            t = threading.Thread(target=_run_clip_generation, args=(client, idx), daemon=True)
            t.start()

    return intro_video_status()
