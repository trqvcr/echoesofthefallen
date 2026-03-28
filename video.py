"""
video.py — Veo video generation for intro cinematic.
"""
import os
import threading
import time

INTRO_VIDEO_PATH = "intro_video.mp4"

INTRO_VIDEO_PROMPT = (
    "Epic dark fantasy cinematic. A dying island consumed by a void rift. "
    "Opening shot: the island from above at dusk — stone ruins, ash-covered plains, a black coastline. "
    "The void rift tears open in the storm clouds above, crimson and obsidian, pulsing with dark energy. "
    "Ash falls like snow. Cut to: robed cultists in a circle performing a ritual around a glowing void shard, "
    "their chanting visible as dark smoke from their mouths. The shard cracks. "
    "The camera pulls back as the rift tears wider. Cinematic dark fantasy, dramatic volumetric lighting, "
    "League of Legends cutscene quality."
)

_generating     = False
_generation_err = None


def intro_video_status() -> str:
    """Returns 'ready', 'generating', 'error', or 'none'."""
    if os.path.exists(INTRO_VIDEO_PATH):
        return "ready"
    if _generating:
        return "generating"
    if _generation_err:
        return "error"
    return "none"


def _run_generation(client):
    global _generating, _generation_err
    try:
        from google.genai.types import GenerateVideosConfig

        print("[veo] starting intro video generation...")
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=INTRO_VIDEO_PROMPT,
            config=GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=8,
            ),
        )

        print("[veo] polling for completion...")
        while not operation.done:
            time.sleep(8)
            operation = client.operations.get(operation)

        video_bytes = operation.response.generated_videos[0].video.video_bytes
        with open(INTRO_VIDEO_PATH, "wb") as f:
            f.write(video_bytes)
        print(f"[veo] intro video saved to {INTRO_VIDEO_PATH}")
    except Exception as e:
        _generation_err = str(e)
        print(f"[veo] generation failed: {e}")
    finally:
        _generating = False


def start_intro_generation(client) -> str:
    """
    Kicks off background Veo generation if not already running/done.
    Returns current status string.
    """
    global _generating, _generation_err

    if os.path.exists(INTRO_VIDEO_PATH):
        return "ready"
    if _generating:
        return "generating"

    if not client:
        return "no_client"

    _generating     = True
    _generation_err = None
    t = threading.Thread(target=_run_generation, args=(client,), daemon=True)
    t.start()
    return "generating"
