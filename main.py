from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize App
app = FastAPI(title="Echoes of the Fallen")

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Gemini Client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 4. Pydantic Models
class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str

class ActionRequest(BaseModel):
    player_id: str
    action: str

# 5. Helpers
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def calculate_derived_stats(attributes: dict, weapon_atk: int = 0, armor_def: int = 0) -> dict:
    """Recalculate derived stats from base attributes + gear."""
    return {
        "max_hp":       20 + (attributes["CON"] * 5),
        "atk":          attributes["STR"] + weapon_atk,
        "def":          armor_def + attributes["CON"] // 2,
        "dodge_chance": attributes["AGI"] * 2
    }

def build_new_player(name: str, race: str, player_class: str, world_state: dict) -> dict:
    """Create a fresh player dict from race + class definitions."""
    race_data  = world_state["races"][race]
    class_data = world_state["classes"][player_class]

    # Base attributes from class, modified by race
    race_mods  = race_data["stat_modifiers"]
    base_attrs = class_data["starting_attributes"].copy()
    attributes = {
        "STR": base_attrs["STR"] + race_mods.get("STR", 0),
        "AGI": base_attrs["AGI"] + race_mods.get("AGI", 0),
        "CON": base_attrs["CON"] + race_mods.get("CON", 0),
        "ARC": base_attrs["ARC"] + race_mods.get("ARC", 0),
    }

    # Starter gear ATK/DEF values per class
    gear_stats = {
        "ashen_knight": {"weapon_atk": 4, "armor_def": 3},
        "void_drifter":  {"weapon_atk": 3, "armor_def": 1},
        "rune_scribe":   {"weapon_atk": 5, "armor_def": 0},
        "void_ranger":   {"weapon_atk": 4, "armor_def": 2},
    }
    g       = gear_stats.get(player_class, {"weapon_atk": 0, "armor_def": 0})
    derived = calculate_derived_stats(attributes, g["weapon_atk"], g["armor_def"])

    # Starting skills at level 1
    skills = {
        skill_id: {"level": 1, "xp": 0, "modifications": []}
        for skill_id in class_data["starting_skills"]
    }

    # Equipped gear slots
    gear = class_data["starting_gear"]
    equipped = {
        "weapon":    gear[0] if len(gear) > 0 else None,
        "armor":     gear[1] if len(gear) > 1 else None,
        "accessory": gear[2] if len(gear) > 2 else None,
    }

    return {
        "name":     name,
        "race":     race,
        "subrace":  None,
        "class":    player_class,
        "subclass": None,
        "status":   "alive",
        "history":  [],
        "location": "ashen_courtyard",
        "hp":           derived["max_hp"],
        "max_hp":       derived["max_hp"],
        "stamina":      10,
        "max_stamina":  10,
        "mana":         5,
        "max_mana":     5,
        "xp":               0,
        "xp_to_next_level": 100,
        "level":            1,
        "attributes":    attributes,
        "derived_stats": derived,
        "skills":    skills,
        "inventory": gear.copy(),
        "equipped":  equipped,
        "milestones": {
            "bosses_defeated":          [],
            "total_kills":              0,
            "total_damage_dealt":       0,
            "total_damage_absorbed":    0,
            "times_nearly_died":        0,
            "skill_modifications_used": 0,
            "subclass_unlocked":        False,
            "subrace_unlocked":         False
        },
        "lineage": [],
        "reputation": {
            "saltmarsh":   0,
            "ashen_ruins": 0,
            "void_wastes": 0
        }
    }

# 6. Serve HTML pages
@app.get("/")
async def serve_login():
    return FileResponse("login.html")

@app.get("/game")
async def serve_game():
    return FileResponse("index.html")

# 7. Health Check
@app.get("/health")
async def health_check():
    return {"message": "Echoes of the Fallen server is running."}

# 8. Register new player
@app.post("/register")
async def register_player(request: RegisterRequest):
    world_state = load_json("world_state.json")

    # Validate race and class
    if request.race not in world_state["races"]:
        raise HTTPException(status_code=400, detail=f"Unknown race: {request.race}")
    if request.player_class not in world_state["classes"]:
        raise HTTPException(status_code=400, detail=f"Unknown class: {request.player_class}")

    # player_id derived from name
    player_id = request.name.lower().replace(" ", "_")

    # If player already exists, resume their session
    if player_id in world_state["players"]:
        existing = world_state["players"][player_id]
        return {
            "player_id": player_id,
            "message":   f"Welcome back, {existing['name']}.",
            "resumed":   True,
            "hp":        existing["hp"],
            "max_hp":    existing["max_hp"],
            "location":  existing["location"],
            "class":     existing["class"],
            "race":      existing["race"],
        }

    # Build and save new player
    new_player = build_new_player(request.name, request.race, request.player_class, world_state)
    world_state["players"][player_id] = new_player
    save_json("world_state.json", world_state)

    return {
        "player_id": player_id,
        "message":   f"The void remembers {request.name}.",
        "resumed":   False,
        "hp":        new_player["hp"],
        "max_hp":    new_player["max_hp"],
        "location":  new_player["location"],
        "class":     new_player["class"],
        "race":      new_player["race"],
    }

# 9. Core Game Loop
@app.post("/action")
async def handle_action(request: ActionRequest):
    world_state = load_json("world_state.json")
    map_data    = load_json("map.json")

    # Get player
    player = world_state["players"].get(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found. Please register first.")

    # Get location
    location_key     = player["location"]
    current_location = map_data.get(location_key)
    if not current_location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Check for movement
    action_lower = request.action.lower()
    for exit_location in current_location.get("exits", []):
        if exit_location.replace("_", " ") in action_lower or exit_location in action_lower:
            player["location"] = exit_location
            current_location   = map_data[exit_location]
            break

    # Race/class flavor for richer prompts
    race_data  = world_state["races"].get(player["race"], {})
    class_data = world_state["classes"].get(player["class"], {})

    # Build Gemini prompt
    prompt = f"""
You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

WORLD HISTORY: {world_state["world_history"]}

CURRENT LOCATION: {current_location["description"]}
LOCATION STATE: {current_location.get("state", {})}
LOCATION HISTORY: {current_location.get("history", [])}
NPCS PRESENT: {list(current_location.get("npcs", {}).keys())}

PLAYER NAME: {player["name"]}
PLAYER RACE: {player["race"]} — {race_data.get("description", "")}
PLAYER CLASS: {player["class"]} — {class_data.get("description", "")}
PLAYER SUBRACE: {player["subrace"]}
PLAYER SUBCLASS: {player["subclass"]}
PLAYER HP: {player["hp"]}/{player["max_hp"]}
PLAYER LEVEL: {player["level"]}
PLAYER SKILLS: {list(player["skills"].keys())}
PLAYER INVENTORY: {player["inventory"]}
PLAYER HISTORY: {player["history"][-5:] if player["history"] else []}

PLAYER ACTION: {request.action}

Respond with vivid narrative (2-3 sentences) that reflects the player's race and class.
Account for location state and NPC memory when relevant.
Then on a new line write:
VISUAL: [one sentence describing the scene for image generation]
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    narrative = response.text

    # Append to player history (keep last 20)
    player["history"].append(f"[{location_key}] {request.action}")
    if len(player["history"]) > 20:
        player["history"] = player["history"][-20:]

    # Save updated world state
    world_state["players"][request.player_id] = player
    save_json("world_state.json", world_state)

    return {
        "text":         narrative,
        "image_base64": "",
        "status":       player["status"],
        "location":     player["location"],
        "hp":           player["hp"],
        "max_hp":       player["max_hp"],
        "level":        player["level"],
        "xp":           player["xp"],
    }