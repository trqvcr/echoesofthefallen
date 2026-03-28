from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os, json
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Echoes of the Fallen")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key and api_key != "placeholder" else None

# ── Pydantic Models ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str

class ActionRequest(BaseModel):
    player_id: str
    action: str
    state: Optional[Dict[str, Any]] = None

# ── JSON Helpers ───────────────────────────────────────────────────────────────

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if "world_state" in path:
            return {"world_history": [], "races": {}, "classes": {}, "skill_definitions": {}}
        if "saves" in path:
            return {}
        return {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"{path} is corrupted. Check your JSON syntax.")

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ── Static Pages ───────────────────────────────────────────────────────────────

@app.get("/")
async def serve_login():
    return FileResponse("login.html")

@app.get("/game")
async def serve_game():
    return FileResponse("index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}

# ── /register ──────────────────────────────────────────────────────────────────

@app.post("/register")
async def register(request: RegisterRequest):
    world_state = load_json("world_state.json")
    saves       = load_json("saves.json")

    # Validate race and class
    if request.race not in world_state["races"]:
        raise HTTPException(status_code=400, detail=f"Unknown race: {request.race}")
    if request.player_class not in world_state["classes"]:
        raise HTTPException(status_code=400, detail=f"Unknown class: {request.player_class}")

    # Build player_id
    player_id = request.name.strip().lower().replace(" ", "_")

    # Resume existing player
    if player_id in saves:
        return {"player_id": player_id, "state": _player_to_state(saves[player_id])}

    # Pull base stats
    race_data  = world_state["races"][request.race]
    class_data = world_state["classes"][request.player_class]

    base = class_data["starting_attributes"]
    mods = race_data["stat_modifiers"]

    STR = base["STR"] + mods.get("STR", 0)
    AGI = base["AGI"] + mods.get("AGI", 0)
    CON = base["CON"] + mods.get("CON", 0)
    ARC = base["ARC"] + mods.get("ARC", 0)

    max_hp      = 20 + CON * 5
    max_stamina = 10
    max_mana    = ARC * 2

    skills = {
        skill_id: {"level": 1, "xp": 0, "modifications": []}
        for skill_id in class_data["starting_skills"]
    }

    player = {
        "name":           request.name.strip(),
        "race":           request.race,
        "subrace":        None,
        "class":          request.player_class,
        "subclass":       None,
        "status":         "alive",
        "history":        [],
        "location":       "ashen_courtyard",
        "hp":             max_hp,
        "max_hp":         max_hp,
        "stamina":        max_stamina,
        "max_stamina":    max_stamina,
        "mana":           max_mana,
        "max_mana":       max_mana,
        "xp":             0,
        "xp_to_next_level": 100,
        "level":          1,
        "attributes":     {"STR": STR, "AGI": AGI, "CON": CON, "ARC": ARC},
        "derived_stats":  {
            "max_hp":       max_hp,
            "atk":          STR + 2,
            "def":          CON // 2,
            "dodge_chance": AGI * 2,
        },
        "skills":    skills,
        "inventory": list(class_data["starting_gear"]),
        "equipped":  {
            "weapon":    class_data["starting_gear"][0] if class_data["starting_gear"] else None,
            "armor":     class_data["starting_gear"][1] if len(class_data["starting_gear"]) > 1 else None,
            "accessory": None,
        },
        "milestones": {
            "bosses_defeated":          [],
            "total_kills":              0,
            "total_damage_dealt":       0,
            "total_damage_absorbed":    0,
            "times_nearly_died":        0,
            "skill_modifications_used": 0,
            "subclass_unlocked":        False,
            "subrace_unlocked":         False,
        },
        "lineage":    [],
        "reputation": {"saltmarsh": 0, "ashen_ruins": 0, "void_wastes": 0},
    }

    saves[player_id] = player
    save_json("saves.json", saves)

    return {"player_id": player_id, "state": _player_to_state(player)}

# ── /action ────────────────────────────────────────────────────────────────────

@app.post("/action")
async def handle_action(request: ActionRequest):
    world_state = load_json("world_state.json")
    map_data    = load_json("map.json")
    saves       = load_json("saves.json")

    player = saves.get(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    location_key     = player["location"]
    current_location = map_data.get(location_key)
    if not current_location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Movement check
    action_lower = request.action.lower()
    for exit_key in current_location.get("exits", []):
        if exit_key.replace("_", " ") in action_lower or exit_key in action_lower:
            player["location"] = exit_key
            current_location   = map_data[exit_key]
            break

    # Append to player history (keep last 20)
    player["history"].append(request.action)
    player["history"] = player["history"][-20:]

    # Build Gemini prompt
    attrs = player["attributes"]
    prompt = f"""You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

WORLD HISTORY: {world_state['world_history']}

LOCATION: {current_location['name']}
DESCRIPTION: {current_location['description']}
LOCATION STATE: {current_location.get('state', {})}
NPCS PRESENT: {list(current_location.get('npcs', {}).keys())}
LOCATION HISTORY: {current_location.get('history', [])[-5:]}

PLAYER: {player['name']} | Race: {player['race']} | Class: {player['class']}
HP: {player['hp']}/{player['max_hp']} | Level: {player['level']}
STR:{attrs['STR']} AGI:{attrs['AGI']} CON:{attrs['CON']} ARC:{attrs['ARC']}
SKILLS: {list(player['skills'].keys())}
INVENTORY: {player['inventory']}
RECENT ACTIONS: {player['history'][-5:]}

PLAYER ACTION: {request.action}

Respond with vivid narrative (2-3 sentences). Then on a new line:
VISUAL: [one sentence describing the scene for image generation]"""

    narrative = "[The void is silent — no AI connected]"
    if client:
        response  = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        narrative = response.text

    # Strip VISUAL line from player-facing text
    display_text = "\n".join(
        line for line in narrative.splitlines()
        if not line.strip().startswith("VISUAL:")
    ).strip()

    # Save player back to saves.json only
    saves[request.player_id] = player
    save_json("saves.json", saves)

    return {
        "text":         display_text,
        "image_base64": "",
        "status":       player["status"],
        "location":     current_location["name"],
        "state":        _player_to_state(player),
    }

# ── State serializer ───────────────────────────────────────────────────────────

def _player_to_state(player: dict) -> dict:
    attrs = player.get("attributes", {})
    return {
        "house_name":       player["name"],
        "player_id":        player["name"].lower().replace(" ", "_"),
        "race":             player["race"],
        "class":            player["class"],
        "status":           player["status"],
        "location":         player["location"],
        "hp":               player["hp"],
        "max_hp":           player["max_hp"],
        "stamina":          player["stamina"],
        "max_stamina":      player["max_stamina"],
        "mana":             player["mana"],
        "max_mana":         player["max_mana"],
        "level":            player["level"],
        "xp":               player["xp"],
        "xp_to_next_level": player["xp_to_next_level"],
        "str":              attrs.get("STR", 0),
        "agi":              attrs.get("AGI", 0),
        "con":              attrs.get("CON", 0),
        "arc":              attrs.get("ARC", 0),
        "inventory":        player["inventory"],
        "equipped":         player.get("equipped", {}),
        "skills":           player.get("skills", {}),
        "milestones":       player.get("milestones", {}),
        "lineage":          player.get("lineage", []),
        "reputation":       player.get("reputation", {}),
    }