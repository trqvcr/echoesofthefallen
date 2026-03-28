import os
import random
import time
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from google import genai
from google.genai.types import GenerateImagesConfig, GenerateContentConfig, Schema, Type
from dotenv import load_dotenv

from models import RegisterRequest, LoginRequest, ActionRequest, RiseRequest, AvatarRequest, TravelRequest
from db import get_player, save_player, get_world, save_world, get_all_locations, save_location, hash_password
from enemies import tick_spawns
from world_tick import tick_world
from combat import player_to_state, _start_combat, process_combat_turn, _make_ancestor_record, build_heir
from images import generate_scene_image, generate_avatar_portrait, generate_npc_portrait
from story import (
    get_story_context, get_story_nudge, check_act_advancement,
    make_world_event, get_active_world_event, STORY_FLAGS,
)
from music import generate_ambient_music, get_music_context
import base64

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

@app.get("/map-bg.jpg")
async def serve_map_bg():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_bg.jpg")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Map background not generated yet. Run generate_map_bg.py")


@app.get("/map.json")
async def serve_map():
    locs = get_all_locations()
    result = {}
    for key, data in locs.items():
        npcs = data.get("npcs", {})
        has_hostile  = any(n.get("disposition", 0) <= -50 and n.get("status") != "dead" for n in npcs.values())
        has_friendly = any(n.get("disposition", 0) > 0  and n.get("status") != "dead" for n in npcs.values())
        result[key] = {
            "name":         data.get("name", key),
            "type":         data.get("type", "location"),
            "parent":       data.get("parent", ""),
            "description":  data.get("description", ""),
            "exits":        data.get("exits", []),
            "x":            data.get("x"),
            "y":            data.get("y"),
            "has_hostile":  has_hostile,
            "has_friendly": has_friendly,
        }
    return result


# ── /events ───────────────────────────────────────────────────────────────────

@app.get("/events")
async def get_events():
    """Polled by clients every few seconds. Returns active world event if any."""
    world = get_world()
    event = get_active_world_event(world.get("story", {}))
    return event or {}


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
        "lineage":           [],
        "reputation":        {"saltmarsh": 0, "ashen_ruins": 0, "void_wastes": 0},
        "combat_state":      {"active": False},
        "visited_locations": ["ashen_courtyard"],
        "travel_progress":   {},
    }

    save_player(player_id, player)
    return {"player_id": player_id, "state": player_to_state(player, player_id)}


# ── /login ─────────────────────────────────────────────────────────────────────

@app.post("/login")
async def login(request: LoginRequest):
    player_id = request.name.strip().lower().replace(" ", "_")
    player    = get_player(player_id)

    if not player:
        raise HTTPException(status_code=404, detail="No character found with that name.")
    if player.get("password_hash") != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    return {"player_id": player_id, "state": player_to_state(player, player_id)}


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
    return {"player_id": player_id, "state": player_to_state(heir, player_id)}


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

    return {"portrait": portrait, "state": player_to_state(player, request.player_id)}


# ── /action ────────────────────────────────────────────────────────────────────

@app.post("/action")
async def handle_action(request: ActionRequest):
    world_state   = get_world()
    all_locations = get_all_locations()
    all_locations = tick_spawns(all_locations)
    all_locations = tick_world(all_locations)

    player = get_player(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    location_key     = player["location"]
    current_location = all_locations.get(location_key, {})
    skill_defs       = world_state.get("skill_definitions", {})

    pre_location = player["location"]
    pre_combat   = player.get("combat_state", {}).get("active", False)

    if pre_combat:
        result = await process_combat_turn(
            player, request.action, current_location,
            location_key, world_state, all_locations,
            request.player_id, skill_defs, client
        )
    else:
        result = await _process_exploration(
            player, request.action, current_location,
            location_key, world_state, all_locations,
            request.player_id, skill_defs
        )

    # Generate ambient music when game context changes
    combat_event  = result.get("combat_event")
    post_location = result.get("state", {}).get("location", pre_location)
    post_combat   = result.get("state", {}).get("combat_state", {}).get("active", False)

    prev_context = get_music_context(pre_location, pre_combat)
    new_context  = get_music_context(post_location, post_combat)

    if new_context != prev_context or combat_event in ("start", "victory", "fled"):
        music_data, music_ctx = generate_ambient_music(client, post_location, post_combat)
        if music_data:
            result["music_base64"]  = music_data
            result["music_context"] = music_ctx

    return result

# ── State Formatter ───────────────────────────────────────────────────────────

def _format_state_for_prompt(state: dict) -> str:
    """Renders location state for Gemini prompts in a readable way.
    Handles both old-format primitives and new-format dicts with metadata."""
    if not state:
        return "none"
    parts = []
    for k, v in state.items():
        if isinstance(v, dict):
            val   = v.get("value", "?")
            desc  = v.get("description", "")
            stages = v.get("stages", [])
            idx   = v.get("stage_index", 0)
            if stages:
                parts.append(f"{k}={val} [stage {idx+1}/{len(stages)}] — {desc}")
            else:
                parts.append(f"{k}={val} — {desc}")
        else:
            parts.append(f"{k}={v}")
    return "; ".join(parts)

# ── Exploration Handler ────────────────────────────────────────────────────────

async def _process_exploration(
    player, action, current_location, location_key,
    world_state, all_locations, player_id, skill_defs
):
    action_lower     = action.lower()
    location_changed = False

    # Self-harm / suicide
    self_harm_keywords = [
        "kill myself", "kill my self", "suicide", "end my life",
        "slay myself", "slit my throat", "stab myself", "end it",
    ]
    if any(kw in action_lower for kw in self_harm_keywords):
        player["hp"]     = 0
        player["status"] = "dead"
        player["history"].append(action)
        player["history"] = player["history"][-20:]
        save_player(player_id, player)
        return {
            "text":         f"{player['name']} chose to end their own life. The void claims another soul.",
            "image_base64": "",
            "status":       "dead",
            "location":     current_location.get("name", location_key),
            "state":        player_to_state(player),
            "combat_event": "death",
            "env_damage":   0,
            "ancestor":     _make_ancestor_record(player),
            "player_id":    player_id,
        }

    # ── Movement ──────────────────────────────────────────────────────────────
    # Direction vectors: x increases east, y increases south (screen space)
    DIRECTION_VECTORS = {
        "north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
        "northeast": (1, -1), "northwest": (-1, -1),
        "southeast": (1, 1),  "southwest": (-1, 1),
        "ne": (1, -1), "nw": (-1, -1), "se": (1, 1), "sw": (-1, 1),
    }

    move_keywords = ["go ", "head ", "move ", "travel ", "walk ", "run ", "proceed "]
    direction_detected = None
    for phrase, vec in DIRECTION_VECTORS.items():
        if any(f"{mv}{phrase}" in action_lower for mv in move_keywords) or action_lower.strip() == phrase:
            direction_detected = (phrase, vec)
            break

    destination_key = None

    if direction_detected:
        _, (dx, dy) = direction_detected
        cx = current_location.get("x")
        cy = current_location.get("y")
        if cx is not None and cy is not None:
            best_score = -1
            for exit_key in current_location.get("exits", []):
                exit_loc = all_locations.get(exit_key, {})
                ex = exit_loc.get("x")
                ey = exit_loc.get("y")
                if ex is None or ey is None:
                    continue
                # Dot product of direction vector with delta to exit
                delta_x = ex - cx
                delta_y = ey - cy
                length  = max(1, abs(delta_x) + abs(delta_y))
                score   = (dx * delta_x + dy * delta_y) / length
                if score > best_score:
                    best_score = score
                    destination_key = exit_key if score > 0 else None

    # Fall back to name-based matching if no direction found (or direction had no good exit)
    if not destination_key:
        for exit_key in current_location.get("exits", []):
            if exit_key.replace("_", " ") in action_lower or exit_key in action_lower:
                destination_key = exit_key
                break

    # ── Multi-step travel: require several moves to cross into a new area ──────
    travel_context = ""  # injected into AI prompt when in transit
    if destination_key and destination_key in all_locations:
        target_loc = all_locations[destination_key]
        cx = current_location.get("x", 0)
        cy = current_location.get("y", 0)
        tx = target_loc.get("x", cx)
        ty = target_loc.get("y", cy)
        dist         = abs(tx - cx) + abs(ty - cy)
        steps_needed = min(4, max(2, dist))

        progress = player.setdefault("travel_progress", {})
        if progress.get("target") == destination_key:
            progress["steps"] = progress.get("steps", 0) + 1
        else:
            # New direction — reset
            progress["target"]       = destination_key
            progress["steps"]        = 1
            progress["steps_needed"] = steps_needed

        steps         = progress["steps"]
        steps_needed  = progress["steps_needed"]

        if steps >= steps_needed:
            # Arrived
            player["location"] = destination_key
            current_location   = all_locations[destination_key]
            location_key       = destination_key
            location_changed   = True
            visited = player.setdefault("visited_locations", ["ashen_courtyard"])
            if destination_key not in visited:
                visited.append(destination_key)
            player["travel_progress"] = {}
        else:
            # Still in transit — stay in current location, inform the AI
            remaining = steps_needed - steps
            travel_context = (
                f"TRAVEL: Player is heading toward {target_loc.get('name', destination_key)} "
                f"({steps}/{steps_needed} steps, {remaining} more needed). "
                f"Narrate their journey through {current_location.get('name', '')} — "
                f"describe what they see as they move in that direction. Do NOT say they arrived."
            )
            destination_key = None  # don't move yet
    elif not direction_detected:
        # Non-movement action — reset travel progress
        player["travel_progress"] = {}

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

        # NPC portrait: generate once, cache in location DB
        npc_portrait = npc_data.get("portrait", "")
        location_dirty_combat = False
        if not npc_portrait and client and npc_data.get("description"):
            npc_portrait = generate_npc_portrait(client, npc_data["name"], npc_data["description"])
            if npc_portrait:
                current_location["npcs"][npc_id]["portrait"] = npc_portrait
                location_dirty_combat = True
        if location_dirty_combat:
            save_location(location_key, current_location)

        return {
            "text":         display_text,
            "image_base64": generate_scene_image(
                client, visual_prompt,
                player.get("avatar_description", ""),
                npc_description=npc_data.get("description", ""),
            ),
            "npc_portrait": npc_portrait,
            "status":       player["status"],
            "location":     current_location["name"],
            "state":        player_to_state(player, player_id),
            "combat_event": "start",
        }

    # Normal exploration
    player["history"].append(action)
    player["history"] = player["history"][-20:]

    # ── Story context + nudge ──────────────────────────────────────────────────
    story               = world_state.setdefault("story", {"act": 1, "flags": {}, "stats": {}, "world_event": None})
    story_ctx           = get_story_context(story)
    turns_no_progress   = player.get("story_turns_without_progress", 0)
    nudge               = get_story_nudge(story, turns_no_progress)

    attrs  = player["attributes"]
    prompt = f"""You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

{story_ctx}
WORLD HISTORY: {world_state['world_history']}
LOCATION: {current_location['name']}
DESCRIPTION: {current_location['description']}
CURRENT STATE: {_format_state_for_prompt(current_location.get('state', {}))}
NPCS HERE: {[f"{k}: {v['name']} (disposition: {v.get('disposition',0)}, status: {v.get('status','alive')})" for k,v in current_location.get('npcs',{}).items()]}
LOCATION HISTORY: {current_location.get('history', [])[-5:]}

PLAYER: {player['name']} | Race: {player['race']} | Class: {player['class']}
HP: {player['hp']}/{player['max_hp']} | Level: {player['level']}
STR:{attrs['STR']} AGI:{attrs['AGI']} CON:{attrs['CON']} ARC:{attrs['ARC']}
SKILLS: {list(player['skills'].keys())}
INVENTORY: {player['inventory']}
RECENT ACTIONS: {player['history'][-5:]}

PLAYER ACTION: {action}
{travel_context}
{nudge}
Respond with vivid narrative (2-3 sentences). Do NOT include any game mechanic notations, inventory updates, state updates, or bracketed annotations in your response — pure prose only."""

    narrative = "[The void is silent — no AI connected]"
    mutation  = {"env_damage": 0, "visual": "", "state_changes": [], "items_gained": [], "npc_id": "", "npc_delta": 0, "npc_memory": "", "history": ""}

    if client:
        # Call 1: narrative
        response  = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        narrative = response.text or "[The void is silent — no AI connected]"

        # Call 2: structured mutations
        mutation_prompt = f"""You are extracting world state changes from a dark fantasy RPG action.

LOCATION: {current_location['name']}
PLAYER: {player['name']}
CURRENT STATE: {_format_state_for_prompt(current_location.get('state', {}))}
NPCS HERE: {list(current_location.get('npcs', {}).keys())}
PLAYER ACTION: {action}
NARRATIVE: {narrative}

Record any physical changes to the environment. If the player touched, broke, moved, marked, or damaged anything — record it.
Only skip truly trivial actions with zero physical effect (looking around, standing still).

For each state_change entry:
- key: snake_case descriptor, e.g. smashed_fountain, name_carved_north_wall, scorched_floor
- value: current state string, e.g. "smashed", "carved", "scorched", "broken", "open"
- description: one sentence including the player's name — what happened
- stages: decay progression if applicable e.g. ["intact","cracked","rubble"] — empty list if permanent
- stage_duration_seconds: seconds per stage. 0 = permanent.

Stage duration guide: broken stone=14400 (4h/stage), broken furniture=0 (permanent), scorched marks=0 (permanent), spilled liquid=1800 (30 min/stage).

items_gained: items the player physically picked up during this action. Each needs id (snake_case), name (display name), description (flavor text noting what it is and where it came from, e.g. "A brittle index finger pried from the dead soldier in the Ashen Courtyard"). Empty list if nothing was taken.

For countable resources (fingers on a body, coins in a pouch, arrows in a quiver):
- On first access, create a state entry tracking the count, e.g. dead_soldier_fingers_remaining="9" (humans have 10 fingers, deduct already taken ones from existing state)
- Decrement the count each time one is taken via a state_change
- If the count is already "0" in the current state, do NOT add to items_gained — nothing left to take

The history field: one sentence in third person with the player's name. Empty string if nothing notable happened."""

        mutation_schema = Schema(
            type=Type.OBJECT,
            properties={
                "env_damage": Schema(type=Type.INTEGER, description="HP damage from environment (falling, traps, fire), 0 if none"),
                "visual":     Schema(type=Type.STRING,  description="One sentence scene description for image generation"),
                "state_changes": Schema(
                    type=Type.ARRAY,
                    description="List of consequential world state changes. Include anything that physically alters the space.",
                    items=Schema(
                        type=Type.OBJECT,
                        properties={
                            "key":                    Schema(type=Type.STRING,  description="Snake_case key, e.g. broken_east_wall, dented_pillar"),
                            "value":                  Schema(type=Type.STRING,  description="Current state value, e.g. broken, dented, scorched, open"),
                            "description":            Schema(type=Type.STRING,  description="One sentence: what changed and who caused it"),
                            "stages":                 Schema(type=Type.ARRAY, items=Schema(type=Type.STRING), description="Ordered decay stages e.g. [intact, cracked, rubble]. Empty list if permanent."),
                            "stage_duration_seconds": Schema(type=Type.INTEGER, description="Seconds per stage transition. 0 means permanent."),
                        }
                    )
                ),
                "items_gained": Schema(
                    type=Type.ARRAY,
                    description="Items the player picked up. Empty if none.",
                    items=Schema(
                        type=Type.OBJECT,
                        properties={
                            "id":          Schema(type=Type.STRING, description="Snake_case item id, e.g. finger_bone, rusty_coin"),
                            "name":        Schema(type=Type.STRING, description="Display name, e.g. 'Index Finger Bone'"),
                            "description": Schema(type=Type.STRING, description="Flavor text with provenance, e.g. 'A brittle index finger taken from the dead soldier in the Ashen Courtyard'"),
                        }
                    )
                ),
                "npc_id":     Schema(type=Type.STRING,  description="NPC id that was affected, empty string if none"),
                "npc_delta":  Schema(type=Type.INTEGER, description="Disposition change for the NPC, 0 if none"),
                "npc_memory": Schema(type=Type.STRING,  description="Memory to append to NPC, empty string if none"),
                "history":    Schema(type=Type.STRING,  description="One sentence for location history log in third person, empty string if nothing significant"),
            },
            required=["env_damage", "visual", "state_changes", "items_gained", "npc_id", "npc_delta", "npc_memory", "history"]
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
        except Exception as e:
            print(f"Mutation extraction failed: {e}")

    display_text = narrative.strip()

    # ── Apply world state mutations ────────────────────────────────────────────
    location_dirty = False

    state_changes = mutation.get("state_changes", [])
    if isinstance(state_changes, list):
        for change in state_changes:
            if not isinstance(change, dict):
                continue
            key = change.get("key", "").strip()
            if not key:
                continue
            if "state" not in current_location:
                current_location["state"] = {}
            stages        = change.get("stages", [])
            stage_duration = int(change.get("stage_duration_seconds", 0))
            value         = change.get("value", "true")
            description   = change.get("description", "")
            if stages and len(stages) > 1:
                stage_index = stages.index(value) if value in stages else 0
                current_location["state"][key] = {
                    "value":         value,
                    "description":   description,
                    "set_at":        time.time(),
                    "stages":        stages,
                    "stage_index":   stage_index,
                    "stage_duration": stage_duration,
                }
            else:
                current_location["state"][key] = {
                    "value":       value,
                    "description": description,
                    "set_at":      time.time(),
                    "permanent":   True,
                }
            location_dirty = True

    items_gained = mutation.get("items_gained", [])
    if isinstance(items_gained, list):
        for item in items_gained:
            if isinstance(item, str) and item:
                player["inventory"].append(item)
            elif isinstance(item, dict) and item.get("id"):
                item["source_location"] = location_key
                player["inventory"].append(item)

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
        current_location.setdefault("history", []).append(history_entry)
        current_location["history"] = current_location["history"][-30:]
        location_dirty = True

    # ── NPC portrait for exploration interactions ─────────────────────────────
    npc_portrait     = ""
    npc_description  = ""
    if npc_id and npc_id in current_location.get("npcs", {}):
        npc_data_exp    = current_location["npcs"][npc_id]
        npc_description = npc_data_exp.get("description", "")
        npc_portrait    = npc_data_exp.get("portrait", "")
        if not npc_portrait and client and npc_description:
            npc_portrait = generate_npc_portrait(client, npc_data_exp.get("name", npc_id), npc_description)
            if npc_portrait:
                current_location["npcs"][npc_id]["portrait"] = npc_portrait
                location_dirty = True

    # ── Scene image: always action-specific; seed reference_image if missing ─────
    visual_prompt = mutation.get("visual", "")
    ref_image     = current_location.get("reference_image", "")

    # For action-driven movement, prefer the narrative's visual prompt so the
    # image reflects what's actually happening on arrival. Fall back to the
    # location description if Gemini didn't produce a visual tag.
    if location_changed and not visual_prompt:
        visual_prompt = f"{current_location.get('name', '')}: {current_location.get('description', '')}"

    scene_img = generate_scene_image(
        client, visual_prompt,
        player.get("avatar_description", ""),
        npc_description=npc_description,
    )
    # Cache as reference_image only if one doesn't exist yet (used by fast travel)
    if scene_img and not ref_image:
        current_location["reference_image"] = scene_img
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
        "image_base64": scene_img,
        "npc_portrait": npc_portrait,
        "status":       player["status"],
        "location":     current_location["name"],
        "state":        player_to_state(player, player_id),
        "env_damage":   env_damage,
    }
    if combat_event:
        result["combat_event"] = combat_event
    result.update(extra_data)
    return result


# ── /travel ────────────────────────────────────────────────────────────────────

@app.post("/travel")
async def fast_travel(request: TravelRequest):
    player = get_player(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.get("combat_state", {}).get("active"):
        raise HTTPException(status_code=400, detail="Cannot fast travel during combat.")

    destination = request.destination
    visited     = player.get("visited_locations", [])

    if destination not in visited:
        raise HTTPException(status_code=403, detail="You have not been to that location yet.")

    all_locations    = get_all_locations()
    current_location = all_locations.get(destination)
    if not current_location:
        raise HTTPException(status_code=404, detail="Location not found.")

    player["location"] = destination
    ref_image          = current_location.get("reference_image", "")
    location_dirty     = False

    if not ref_image and client:
        loc_prompt = f"{current_location.get('name', destination)}: {current_location.get('description', '')}"
        ref_image  = generate_scene_image(client, loc_prompt, player.get("avatar_description", ""))
        if ref_image:
            current_location["reference_image"] = ref_image
            location_dirty = True

    if location_dirty:
        save_location(destination, current_location)

    save_player(request.player_id, player)

    return {
        "text":         f"You travel swiftly to {current_location.get('name', destination)}.",
        "image_base64": ref_image,
        "location":     current_location.get("name", destination),
        "state":        player_to_state(player, request.player_id),
    }
