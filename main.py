from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- 1. MODELS (Defined here to avoid conflicts) ---
class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str

class ActionRequest(BaseModel):
    player_id: str
    action: str
    state: Dict[str, Any] 

# --- 2. INITIALIZE APP & CORS ---
app = FastAPI(title="Echoes of the Fallen")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. GEMINI CLIENT ---
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key and api_key != "placeholder" else None
NANO_BANANA_URL = os.getenv("NANO_BANANA_URL", "http://your-image-api.com/generate")

# --- 4. CORE HELPERS ---
def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if "world_state" in path:
            return {"world_history": [], "races": {}, "classes": {}, "skill_definitions": {}, "players": {}}
        return {}
    except json.JSONDecodeError:
         raise HTTPException(status_code=500, detail=f"{path} is corrupted. Check your JSON syntax.")

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def calculate_derived_stats(attributes: dict, weapon_atk: int = 0, armor_def: int = 0) -> dict:
    return {
        "max_hp":       20 + (attributes["CON"] * 5),
        "atk":          attributes["STR"] + weapon_atk,
        "def":          armor_def + (attributes["CON"] // 2),
        "dodge_chance": attributes["AGI"] * 2
    }

def build_new_player(name: str, race: str, player_class: str, rules: dict) -> dict:
    race_data  = rules.get("races", {}).get(race, {"stat_modifiers": {}})
    class_data = rules.get("classes", {}).get(player_class, {"starting_attributes": {"STR": 5, "AGI": 5, "CON": 5, "ARC": 5}, "starting_gear": [], "starting_skills": []})

    race_mods  = race_data.get("stat_modifiers", {})
    base_attrs = class_data.get("starting_attributes", {})
    attributes = {
        "STR": base_attrs.get("STR", 0) + race_mods.get("STR", 0),
        "AGI": base_attrs.get("AGI", 0) + race_mods.get("AGI", 0),
        "CON": base_attrs.get("CON", 0) + race_mods.get("CON", 0),
        "ARC": base_attrs.get("ARC", 0) + race_mods.get("ARC", 0),
    }

    gear_stats = {
        "ashen_knight": {"weapon_atk": 4, "armor_def": 3},
        "void_drifter": {"weapon_atk": 3, "armor_def": 1},
        "rune_scribe":  {"weapon_atk": 5, "armor_def": 0},
        "void_ranger":  {"weapon_atk": 4, "armor_def": 2},
    }
    g = gear_stats.get(player_class, {"weapon_atk": 0, "armor_def": 0})
    derived = calculate_derived_stats(attributes, g["weapon_atk"], g["armor_def"])
    gear = class_data.get("starting_gear", [])

    return {
        "name":         name,
        "house_name":   name, # Syncing frontend and backend keys
        "race":         race,
        "subrace":      None,
        "class":        player_class,
        "subclass":     None,
        "status":       "alive",
        "history":      [], 
        "location":     "ashen_courtyard", 
        "current_room": "ashen_courtyard",
        "hp":           derived["max_hp"],
        "max_hp":       derived["max_hp"],
        "strength":     attributes["STR"], 
        "agility":      attributes["AGI"],
        "constitution": attributes["CON"],
        "arcane":       attributes["ARC"],
        "derived_stats": derived,
        "stamina":      10,
        "max_stamina":  10,
        "mana":         5,
        "max_mana":     5,
        "xp":           0,
        "xp_to_next_level": 100,
        "level":        1,
        "inventory":    gear.copy(),
        "equipped": {
            "weapon":    gear[0] if len(gear) > 0 else None,
            "armor":     gear[1] if len(gear) > 1 else None,
            "accessory": gear[2] if len(gear) > 2 else None,
        },
        "skills":       class_data.get("starting_skills", []),
        "milestones": {
            "bosses_defeated": [],
            "total_kills": 0,
            "times_nearly_died": 0
        },
        "lineage":      [], 
        "reputation": { "saltmarsh": 0, "ashen_ruins": 0, "void_wastes": 0 }
    }

# --- 5. AI DM PARSER ---
def parse_dm_output(response_text: str) -> tuple[str, str]:
    match = re.search(r'VISUAL:\s*(.*)', response_text, re.IGNORECASE)
    if match:
        return response_text[:match.start()].strip(), match.group(1).strip()
    return response_text.strip(), ""

def generate_void_image(prompt: str) -> str:
    if not prompt or NANO_BANANA_URL == "http://your-image-api.com/generate":
        return ""
    try:
        return "" 
    except Exception as e:
        print(f"Image Generation Failed: {e}")
        return ""

# --- 6. ROUTES ---
@app.get("/")
async def serve_login():
    return FileResponse("login.html")

@app.get("/game")
async def serve_game():
    return FileResponse("index.html")

@app.get("/health")
async def health_check():
    return {"message": "Echoes of the Fallen server is running."}

@app.post("/register")
async def register_player(request: RegisterRequest):
    world_state = load_json("world_state.json")

    if not world_state.get("races") or not world_state.get("classes"):
         raise HTTPException(status_code=500, detail="world_state.json is missing or corrupted (Races/Classes not found).")

    if request.race not in world_state["races"]:
        raise HTTPException(status_code=400, detail=f"Unknown race: {request.race}")
    if request.player_class not in world_state["classes"]:
        raise HTTPException(status_code=400, detail=f"Unknown class: {request.player_class}")

    player_id = request.name.lower().replace(" ", "_")

    if player_id in world_state.get("players", {}):
        existing = world_state["players"][player_id]
        return {
            "player_id": player_id,
            "message":   f"Welcome back, {existing.get('name', 'Wanderer')}.",
            "resumed":   True,
            "hp":        existing.get("hp", 20),
            "max_hp":    existing.get("max_hp", 20),
            "state":     existing 
        }

    new_player = build_new_player(request.name, request.race, request.player_class, world_state)
    world_state.setdefault("players", {})[player_id] = new_player
    save_json("world_state.json", world_state)

    return {
        "message": "Character forged in the void.",
        "player_id": player_id,
        "hp": new_player["hp"],
        "max_hp": new_player["max_hp"],
        "state": new_player 
    }

@app.post("/action")
async def handle_action(request: ActionRequest):
    world_state = load_json("world_state.json")
    map_data    = load_json("map.json")

    player = world_state.get("players", {}).get(request.player_id)
    if not player:
        player = request.state 

    action = request.action.lower()
    room_id = player.get("location", player.get("current_room", "ashen_courtyard"))
    room = map_data.get(room_id, map_data.get("ashen_courtyard", {}))
    
    for exit_location in room.get("exits", []):
        if exit_location.replace("_", " ") in action or exit_location in action:
            player["location"] = exit_location
            player["current_room"] = exit_location
            room = map_data.get(exit_location, {})
            action = f"moves to {exit_location.replace('_', ' ')}."
            break

    race_data  = world_state.get("races", {}).get(player.get("race", "human"), {})
    class_data = world_state.get("classes", {}).get(player.get("class", "ashen_knight"), {})
    
    history = player.setdefault("history", [])
    history.append(f"[{room_id}] {request.action}")
    if len(history) > 5:
        history.pop(0)

    prompt = f"""
You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

WORLD HISTORY: {world_state.get("world_history", [])}

CURRENT LOCATION: {room.get('description', 'A dark void.')}
LOCATION STATE: {room.get("state", {})}
LOCATION HISTORY: {room.get("history", [])}
NPCS PRESENT: {list(room.get("npcs", {}).keys())}

PLAYER NAME: {player.get("house_name", player.get("name"))}
PLAYER RACE: {player.get("race")} — {race_data.get("description", "")}
PLAYER CLASS: {player.get("class")} — {class_data.get("description", "")}
PLAYER HP: {player.get("hp")}/{player.get("max_hp")}
PLAYER LEVEL: {player.get("level", 1)}
PLAYER SKILLS: {player.get("skills", [])}
PLAYER INVENTORY: {player.get("inventory", [])}
PLAYER HISTORY (LAST 5): {history}

PLAYER ACTION: {action}

Respond with vivid narrative (2-3 sentences) that reflects the player's race and class.
Account for location state and NPC memory when relevant. Do not offer a list of choices.
Then on a new line write:
VISUAL: [one sentence describing the scene for image generation]
"""

    dm_raw_text = "The AI is asleep. Set your GEMINI_API_KEY."
    if client:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            dm_raw_text = response.text
        except Exception as e:
            dm_raw_text = f"The void ripples with an error: {str(e)}"

    narrative_output, visual_generation_prompt = parse_dm_output(dm_raw_text)
    generated_image_base64 = generate_void_image(visual_generation_prompt)

    world_state.setdefault("players", {})[request.player_id] = player
    save_json("world_state.json", world_state)

    return {
        "text":         narrative_output,
        "image_base64": generated_image_base64, 
        "state":        player, 
        "location":     room.get('name', 'Unknown'),
        "status":       player.get("status", "alive")
    }