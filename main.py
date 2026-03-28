import os
import random
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from google import genai
from google.genai.types import GenerateImagesConfig, GenerateContentConfig, Schema, Type
from dotenv import load_dotenv

from models import RegisterRequest, LoginRequest, ActionRequest, RiseRequest, AvatarRequest
from db import get_player, save_player, get_world, get_all_locations, save_location, hash_password
from enemies import tick_spawns
from combat import player_to_state, _start_combat, process_combat_turn, _make_ancestor_record, build_heir
from images import generate_scene_image, generate_avatar_portrait
import base64;

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
client  = genai.Client(api_key=api_key) if api_key and api_key != "placeholder" else None


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

@app.get("/map.json")
async def serve_map():
    return get_all_locations()


# ── /register ──────────────────────────────────────────────────────────────────

@app.post("/register")
async def register(request: RegisterRequest):
    world_state = get_world()

    if request.race not in world_state["races"]:
        raise HTTPException(status_code=400, detail=f"Unknown race: {request.race}")
    if request.player_class not in world_state["classes"]:
        raise HTTPException(status_code=400, detail=f"Unknown class: {request.player_class}")
    if not request.password or len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")

    player_id = request.name.strip().lower().replace(" ", "_")

    if get_player(player_id):
        raise HTTPException(status_code=400, detail="That name is already taken. Please login instead.")

    race_data  = world_state["races"][request.race]
    class_data = world_state["classes"][request.player_class]
    base       = class_data["starting_attributes"]
    mods       = race_data["stat_modifiers"]

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
        "name":             request.name.strip(),
        "password_hash":    hash_password(request.password),
        "race":             request.race,
        "subrace":          None,
        "class":            request.player_class,
        "subclass":         None,
        "status":           "alive",
        "history":          [],
        "location":         "ashen_courtyard",
        "hp":               max_hp,
        "max_hp":           max_hp,
        "stamina":          max_stamina,
        "max_stamina":      max_stamina,
        "mana":             max_mana,
        "max_mana":         max_mana,
        "xp":               0,
        "xp_to_next_level": 100,
        "level":            1,
        "attributes":       {"STR": STR, "AGI": AGI, "CON": CON, "ARC": ARC},
        "derived_stats":    {
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
        "lineage":      [],
        "reputation":   {"saltmarsh": 0, "ashen_ruins": 0, "void_wastes": 0},
        "combat_state": {"active": False},
    }

    save_player(player_id, player)
    return {"player_id": player_id, "state": player_to_state(player)}


# ── /login ─────────────────────────────────────────────────────────────────────

@app.post("/login")
async def login(request: LoginRequest):
    player_id = request.name.strip().lower().replace(" ", "_")
    player    = get_player(player_id)

    if not player:
        raise HTTPException(status_code=404, detail="No character found with that name.")
    if player.get("password_hash") != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    return {"player_id": player_id, "state": player_to_state(player)}


# ── /rise ──────────────────────────────────────────────────────────────────────

@app.post("/rise")
async def rise_as_heir(request: RiseRequest):
    player_id   = request.player_id
    dead_player = get_player(player_id)

    if not dead_player:
        raise HTTPException(status_code=404, detail="Player not found")
    if dead_player.get("status") != "dead":
        raise HTTPException(status_code=400, detail="Player is not dead")

    heir_name = request.heir_name.strip()
    if not heir_name:
        raise HTTPException(status_code=400, detail="Heir name cannot be empty")

    heir = build_heir(dead_player, heir_name)
    save_player(player_id, heir)
    return {"player_id": player_id, "state": player_to_state(heir)}


# ── /avatar ────────────────────────────────────────────────────────────────────

@app.post("/avatar")
async def set_avatar(request: AvatarRequest):
    player = get_player(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    description = request.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    portrait = generate_avatar_portrait(client, description)

    player["avatar_description"] = description
    player["avatar_portrait"]    = portrait
    save_player(request.player_id, player)

    return {"portrait": portrait, "state": player_to_state(player)}


# ── /action ────────────────────────────────────────────────────────────────────

@app.post("/action")
async def handle_action(request: ActionRequest):
    world_state   = get_world()
    all_locations = get_all_locations()
    all_locations = tick_spawns(all_locations)

    player = get_player(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    location_key     = player["location"]
    current_location = all_locations.get(location_key, {})
    skill_defs       = world_state.get("skill_definitions", {})

    if player.get("combat_state", {}).get("active"):
        return await process_combat_turn(
            player, request.action, current_location,
            location_key, world_state, all_locations,
            request.player_id, skill_defs, client
        )
    else:
        return await _process_exploration(
            player, request.action, current_location,
            location_key, world_state, all_locations,
            request.player_id, skill_defs
        )

# ── Exploration Handler ────────────────────────────────────────────────────────

async def _process_exploration(
    player, action, current_location, location_key,
    world_state, all_locations, player_id, skill_defs
):
    action_lower = action.lower()

    # Movement
    for exit_key in current_location.get("exits", []):
        if exit_key.replace("_", " ") in action_lower or exit_key in action_lower:
            player["location"] = exit_key
            current_location   = all_locations.get(exit_key, {})
            location_key       = exit_key
            break

    # Combat initiation
    npcs             = current_location.get("npcs", {})
    combat_initiated = None
    first_turn       = "player"

    attack_keywords = ["attack", "fight", "kill", "stab", "strike", "hit", "punch", "charge", "ambush"]
    if any(kw in action_lower for kw in attack_keywords):
        for npc_id, npc_data in npcs.items():
            if npc_data.get("status") == "dead":
                continue
            if any(word in action_lower for word in npc_data["name"].lower().split()):
                combat_initiated = (npc_id, npc_data)
                break

    if not combat_initiated:
        for npc_id, npc_data in npcs.items():
            if npc_data.get("status") == "dead":
                continue
            if npc_data.get("disposition", 0) <= -50:
                combat_initiated = (npc_id, npc_data)
                first_turn       = "enemy"
                break

    if combat_initiated:
        npc_id, npc_data = combat_initiated
        player = _start_combat(player, npc_id, npc_data, first_turn)
        attrs  = player["attributes"]

        combat_prompt = f"""You are a dark fantasy dungeon master for 'Echoes of the Fallen'.
Combat has just begun!

LOCATION: {current_location['name']}
PLAYER: {player['name']} | {player['race']} {player['class']} | HP: {player['hp']}/{player['max_hp']}
STR:{attrs['STR']} AGI:{attrs['AGI']} CON:{attrs['CON']} ARC:{attrs['ARC']}
SKILLS: {list(player['skills'].keys())}

ENEMY: {npc_data['name']} | HP: {npc_data['hp']}/{npc_data['max_hp']} | ATK: {npc_data['atk']} DEF: {npc_data['def']}
ENEMY DESCRIPTION: {npc_data.get('description', '')}

PLAYER ACTION: {action}
FIRST TURN: {first_turn}

Narrate the start of combat vividly (2-3 sentences).
Then output EXACTLY on a new line:
VISUAL: [scene description for image generation]"""

        narrative = "[Combat begins]"
        raw_text  = ""
        if client:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=combat_prompt)
            raw_text = response.text or ""
            narrative = raw_text or "[Combat begins]"

        visual_prompt = next(
            (l.split(":", 1)[1].strip() for l in raw_text.splitlines() if l.strip().startswith("VISUAL:")),
            ""
        )
        display_text = "\n".join(
            line for line in narrative.splitlines()
            if not line.strip().startswith("VISUAL:")
        ).strip()

        player["history"].append(f"[COMBAT STARTED] vs {npc_data['name']}")
        player["history"] = player["history"][-20:]
        save_player(player_id, player)

        return {
            "text":         display_text,
            "image_base64": generate_scene_image(client, visual_prompt, player.get("avatar_description", "")),
            "status":       player["status"],
            "location":     current_location["name"],
            "state":        player_to_state(player),
            "combat_event": "start",
        }

    # Normal exploration
    player["history"].append(action)
    player["history"] = player["history"][-20:]

    attrs  = player["attributes"]
    prompt = f"""You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

WORLD HISTORY: {world_state['world_history']}
LOCATION: {current_location['name']}
DESCRIPTION: {current_location['description']}
CURRENT STATE FLAGS: {current_location.get('state', {})}
NPCS HERE: {[f"{k}: {v['name']} (disposition: {v.get('disposition',0)}, status: {v.get('status','alive')})" for k,v in current_location.get('npcs',{}).items()]}
LOCATION HISTORY: {current_location.get('history', [])[-5:]}

PLAYER: {player['name']} | Race: {player['race']} | Class: {player['class']}
HP: {player['hp']}/{player['max_hp']} | Level: {player['level']}
STR:{attrs['STR']} AGI:{attrs['AGI']} CON:{attrs['CON']} ARC:{attrs['ARC']}
SKILLS: {list(player['skills'].keys())}
INVENTORY: {player['inventory']}
RECENT ACTIONS: {player['history'][-5:]}

PLAYER ACTION: {action}

Respond with vivid narrative (2-3 sentences)."""

    narrative = "[The void is silent — no AI connected]"
    mutation  = {"env_damage": 0, "visual": "", "state_changes": {}, "npc_id": "", "npc_delta": 0, "npc_memory": "", "history": ""}

    if client:
        # Call 1: narrative
        response  = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        narrative = response.text or "[The void is silent — no AI connected]"

        # Call 2: structured mutations
        mutation_prompt = f"""Given this game action and its narrative, extract the world state changes.

LOCATION: {current_location['name']}
CURRENT STATE FLAGS: {current_location.get('state', {})}
NPCS HERE: {list(current_location.get('npcs', {}).keys())}
PLAYER ACTION: {action}
NARRATIVE: {narrative}

Extract what changed."""

        mutation_schema = Schema(
            type=Type.OBJECT,
            properties={
                "env_damage":    Schema(type=Type.INTEGER, description="HP damage from environment, 0 if none"),
                "visual":        Schema(type=Type.STRING,  description="One sentence scene description for image generation"),
                "state_changes": Schema(type=Type.OBJECT,  description="State flags that changed, e.g. broken_table:true. Invent new keys freely."),
                "npc_id":        Schema(type=Type.STRING,  description="NPC id that was affected, empty string if none"),
                "npc_delta":     Schema(type=Type.INTEGER, description="Disposition change for the NPC, 0 if none"),
                "npc_memory":    Schema(type=Type.STRING,  description="Memory to append to NPC, empty string if none"),
                "history":       Schema(type=Type.STRING,  description="One sentence for location history log, empty string if nothing significant"),
            },
            required=["env_damage", "visual", "state_changes", "npc_id", "npc_delta", "npc_memory", "history"]
        )

        try:
            mut_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=mutation_prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=mutation_schema
                )
            )
            mutation = json.loads(mut_response.text)
            print(f"=== MUTATION ===\n{mutation}\n================")
        except Exception as e:
            print(f"Mutation extraction failed: {e}")

    display_text = narrative.strip()

    # ── Apply world state mutations ────────────────────────────────────────────
    location_dirty = False

    state_changes = mutation.get("state_changes", {})
    if isinstance(state_changes, dict) and state_changes:
        if "state" not in current_location:
            current_location["state"] = {}
        current_location["state"].update(state_changes)
        location_dirty = True

    npc_id     = mutation.get("npc_id", "")
    npc_delta  = mutation.get("npc_delta", 0)
    npc_memory = mutation.get("npc_memory", "")
    if npc_id and npc_id in current_location.get("npcs", {}):
        if npc_delta:
            current_location["npcs"][npc_id]["disposition"] = current_location["npcs"][npc_id].get("disposition", 0) + npc_delta
        if npc_memory:
            current_location["npcs"][npc_id].setdefault("memory", []).append(npc_memory)
        location_dirty = True

    history_entry = mutation.get("history", "")
    if history_entry:
        current_location.setdefault("history", []).append(f"[{player['name']}] {history_entry}")
        location_dirty = True

    if location_dirty:
        save_location(location_key, current_location)

    # ── Environmental damage ───────────────────────────────────────────────────
    combat_event = None
    extra_data   = {}
    env_damage   = max(0, int(mutation.get("env_damage", 0)))

    if env_damage > 0:
        player["hp"] = max(0, player["hp"] - env_damage)
        player["milestones"]["total_damage_absorbed"] += env_damage

        if player["hp"] <= 0:
            player["status"] = "dead"
            player["hp"]     = 0
            combat_event     = "death"
            save_player(player_id, player)
            extra_data = {"ancestor": _make_ancestor_record(player), "player_id": player_id}

    if combat_event != "death":
        save_player(player_id, player)

    result = {
        "text":         display_text,
        "image_base64": generate_scene_image(client, mutation.get("visual", ""), player.get("avatar_description", "")),
        "status":       player["status"],
        "location":     current_location["name"],
        "state":        player_to_state(player),
        "env_damage":   env_damage,
    }
    if combat_event:
        result["combat_event"] = combat_event
    result.update(extra_data)
    return result
