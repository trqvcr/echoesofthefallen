from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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

# 3. Gemini Client (Crash-proof)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key and api_key != "placeholder" else None

# 4. Pydantic Models
class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str

class ActionRequest(BaseModel):
    player_id: str
    action: str
    # Changed to Dict to seamlessly accept the complex new state without validation errors
    state: Dict[str, Any] 

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
        "def":          armor_def + (attributes["CON"] // 2),
        "dodge_chance": attributes["AGI"] * 2
    }

def build_new_player(name: str, race: str, player_class: str, rules: dict) -> dict:
    """Create a fresh player dict from race + class definitions."""
    race_data  = rules["races"][race]
    class_data = rules["classes"][player_class]

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
        "void_drifter": {"weapon_atk": 3, "armor_def": 1},
        "rune_scribe":  {"weapon_atk": 5, "armor_def": 0},
        "void_ranger":  {"weapon_atk": 4, "armor_def": 2},
    }
    g = gear_stats.get(player_class, {"weapon_atk": 0, "armor_def": 0})
    derived = calculate_derived_stats(attributes, g["weapon_atk"], g["armor_def"])
    gear = class_data["starting_gear"]

    # Mapped to match the frontend's expected UI structure while keeping advanced stats
    return {
        "house_name":   name,
        "race":         race,
        "class":        player_class,
        "current_room": "ashen_courtyard", 
        "hp":           derived["max_hp"],
        "max_hp":       derived["max_hp"],
        "strength":     attributes["STR"], 
        "agility":      attributes["AGI"],
        "constitution": attributes["CON"],
        "arcane":       attributes["ARC"],
        "stamina":      10,
        "mana":         5,
        "xp":           0,
        "level":        1,
        "inventory":    gear.copy(),
        "equipped": {
            "weapon":    gear[0] if len(gear) > 0 else None,
            "armor":     gear[1] if len(gear) > 1 else None,
            "accessory": gear[2] if len(gear) > 2 else None,
        },
        "derived_stats": derived,
        "skills":       class_data["starting_skills"],
        "history":      [],
        "dead_ancestors": [],
        "current_enemy": None
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

# 8. Registration Endpoint
@app.post("/register")
async def register_player(request: RegisterRequest):
    try:
        # Changed to world_state.json
        rules = load_json("world_state.json")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="world_state.json is missing! Please make sure it is in the folder.")

    if request.race not in rules.get("races", {}):
        raise HTTPException(status_code=400, detail=f"Unknown race: {request.race}")
    if request.player_class not in rules.get("classes", {}):
        raise HTTPException(status_code=400, detail=f"Unknown class: {request.player_class}")

    # Build state using your teammate's advanced logic
    initial_state = build_new_player(request.name, request.race, request.player_class, rules)
    
    return {
        "message": "Character forged in the void.",
        "player_id": request.name.lower().replace(" ", "_"),
        "hp": initial_state["hp"],
        "max_hp": initial_state["max_hp"],
        "state": initial_state
    }

# 9. Core Game Loop
@app.post("/action")
async def handle_action(request: ActionRequest):
    game_state = request.state
    action = request.action.lower()
    
    try:
        world_map = load_json("map.json")
        # Changed to world_state.json
        rules = load_json("world_state.json")
    except FileNotFoundError:
        return {"text": "System Error: The archives (JSON files) are missing.", "state": game_state, "status": "alive"}

    # Get Location Data
    room_id = game_state.get("current_room", "ashen_courtyard")
    room = world_map.get(room_id, world_map.get("ashen_courtyard", {}))
    
    # Movement Logic
    for exit_location in room.get("exits", []):
        if exit_location.replace("_", " ") in action or exit_location in action:
            game_state["current_room"] = exit_location
            room = world_map[exit_location]
            action = f"moves to {exit_location.replace('_', ' ')}."
            break

    # Extract Lore Data
    race_data  = rules.get("races", {}).get(game_state.get("race", "human"), {})
    class_data = rules.get("classes", {}).get(game_state.get("class", "ashen_knight"), {})
    
    # Update Player History for Gemini Context
    history = game_state.setdefault("history", [])
    history.append(f"[{room_id}] {request.action}")
    if len(history) > 5:
        history.pop(0)

    # Your Teammate's Advanced Gemini DM Prompt
    prompt = f"""
You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

WORLD HISTORY: {rules.get("world_history", [])}

CURRENT LOCATION: {room.get('description', 'A dark void.')}
LOCATION STATE: {room.get("state", {})}
LOCATION HISTORY: {room.get("history", [])}
NPCS PRESENT: {list(room.get("npcs", {}).keys())}

PLAYER NAME: {game_state.get("house_name")}
PLAYER RACE: {game_state.get("race")} — {race_data.get("description", "")}
PLAYER CLASS: {game_state.get("class")} — {class_data.get("description", "")}
PLAYER HP: {game_state.get("hp")}/{game_state.get("max_hp")}
PLAYER LEVEL: {game_state.get("level", 1)}
PLAYER SKILLS: {game_state.get("skills", [])}
PLAYER INVENTORY: {game_state.get("inventory", [])}
PLAYER HISTORY: {history}

PLAYER ACTION: {action}

Respond with vivid narrative (2-3 sentences) that reflects the player's race and class.
Account for location state and NPC memory when relevant. Do not offer a list of choices.
Then on a new line write:
VISUAL: [one sentence describing the scene for image generation]
"""

    if client:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash', # <-- THIS IS THE FIX
                contents=prompt
            )
            response_text = response.text
        except Exception as e:
            response_text = f"The void ripples with an error: {str(e)}"
    else:
        response_text = "The AI is asleep. Set your GEMINI_API_KEY."

    return {
        "text": response_text,
        "state": game_state,
        "location": room.get('name', 'Unknown'),
        "status": "alive"
    }