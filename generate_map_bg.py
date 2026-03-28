"""
generate_map_bg.py — generates the world map background image.
Run once: python generate_map_bg.py
Output: map_bg.jpg in the project directory.
Safe to re-run to regenerate.
"""
import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateImagesConfig

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT = (
    "Aerial top-down dark fantasy map illustration. "
    "A single fractured stone island floating in infinite starless void. "
    "Painted in the style of a League of Legends map — rich detail, "
    "dark atmospheric, slightly isometric bird's-eye view. "

    "LEFT THIRD — The Ashen Ruins: "
    "Crumbled ancient imperial stone district. Broken temples, collapsed "
    "fortress towers, cracked stone archways, shattered pillars half-buried "
    "in grey ash. Dead bare-branched trees with grey bark. Thick ash dunes. "
    "A flooded sunken quarter in the lower-left with still black void-water "
    "pools that reflect faint violet light. Cracked grave markers and "
    "overgrown burial mounds. A leaning stone watchtower on the north edge. "

    "CENTER — The Bridge Zone: "
    "A wide stone bridge arching over a glowing void rift. Cold blue-violet "
    "energy rises from the dark chasm. A small abandoned camp with "
    "weatherbeaten canvas tents and a cold firepit beside the bridge. "

    "RIGHT THIRD — Saltmarsh Settlement: "
    "A dense medieval settlement of dark stone buildings with amber lantern "
    "glow in windows, cobblestone alleys, a prominent tavern with a hanging "
    "sign, a busy market square with stalls, a barracks building, and wooden "
    "docks extending over the island's edge. Rope bridges between structures. "
    "Warm amber and orange light contrast the darkness. "

    "TOP SECTION — The Void Wastes: "
    "Barren cracked black obsidian and volcanic rock. Deep glowing red fissures "
    "of void energy run through the ground. No vegetation whatsoever. "
    "A needle-like rock spire at the far edge. The ground faintly pulses "
    "with crimson light. "

    "EDGES: The island's stone cliffs drop sharply into infinite black void. "
    "Faint distant purple stars far below. "

    "COLOR PALETTE: deep purples, near-black, muted dark grey, blood red "
    "accents, dark amber warmth on the right side only. "
    "High detail, painterly, cinematic lighting, no UI elements, no text, "
    "no grid lines."
)

print("Generating map background...")
print(f"Prompt length: {len(PROMPT)} chars")

result = client.models.generate_images(
    model="imagen-4.0-fast-generate-001",
    prompt=PROMPT,
    config=GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="16:9",
        output_mime_type="image/jpeg",
    ),
)

if result.generated_images:
    img_bytes = result.generated_images[0].image.image_bytes
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_bg.jpg")
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    size_kb = len(img_bytes) // 1024
    print(f"Saved: {out_path} ({size_kb} KB)")
else:
    print("Generation failed — no images returned.")
