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
    "Directly overhead top-down satellite view of an entire small stone island "
    "floating in infinite void space. The whole island fits within the frame "
    "with void surrounding all edges. Extreme altitude — like looking straight "
    "down from thousands of feet above. No perspective, no isometric angle, "
    "perfectly flat top-down orthographic view. Dark fantasy painted map art. "

    "The island is divided into distinct regions visible as color zones: "

    "LEFT — Ashen Ruins: A grey-purple ash-covered district. Crumbled stone "
    "ruins visible only as tiny dark specks and grey rubble patches. Dead "
    "forests as clusters of dark grey dots. Ash dunes as pale grey smears. "
    "A small dark void-water pool in the lower-left corner. "

    "CENTER — Bridge and Wasteland: A thin stone bridge crossing a glowing "
    "blue-violet void rift (a dark crack with glowing edges). "

    "RIGHT — Saltmarsh Settlement: A dense cluster of tiny amber-lit specks "
    "suggesting tightly packed buildings. Warm orange-amber color wash over "
    "the district. Tiny dock structures at the very right edge over void. "

    "TOP — Void Wastes: Barren black cracked obsidian. Glowing red fissure "
    "lines running through the rock. No features, just cracked dark stone "
    "with red void energy seeping through cracks. "

    "The island edges are sharp rocky cliffs dropping into infinite black void. "
    "The void surrounding the island is deep black with faint distant stars. "
    "Thin winding paths visible as slightly lighter lines between regions. "

    "Style: painterly dark fantasy cartography, perfectly top-down orthographic, "
    "the entire island small within the frame, individual buildings indistinct "
    "— only color, texture, and region shape matter. Muted dark palette: "
    "ash grey, near-black, blood red cracks, faint amber glow on right. "
    "No UI, no text, no labels, no grid."
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
