from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os, json, random
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

class LevelUpRequest(BaseModel):
    player_id: str
    stat_to_increase: str

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

# ── Combat Helpers ─────────────────────────────────────────────────────────────

def _calc_player_damage_range(player: dict, skill_id: Optional[str], skill_defs: dict) -> tuple:
    """Return (min_dmg, max_dmg) for player attack."""
    attrs    = player["attributes"]
    base_atk = player["derived_stats"]["atk"]

    if skill_id and skill_id in skill_defs:
        skill     = skill_defs[skill_id]
        base_dmg  = skill["base_damage"]
        scale_key = skill.get("scales_with", "STR")
        scale_val = attrs.get(scale_key, 0)
        min_dmg   = max(1, base_dmg + scale_val // 2)
        max_dmg   = base_dmg + scale_val
    else:
        min_dmg = max(1, base_atk - 2)
        max_dmg = base_atk + 2

    return (min_dmg, max_dmg)

def _calc_enemy_damage_range(enemy: dict, player_def: int) -> tuple:
    """Return (min_dmg, max_dmg) for enemy attack after applying player DEF."""
    raw_min = max(0, enemy["atk"] - player_def - 1)
    raw_max = max(1, enemy["atk"] - player_def + 2)
    return (raw_min, raw_max)

def _start_combat(player: dict, enemy_id: str, enemy_data: dict, first_turn: str) -> dict:
    """Attach combat_state to player. first_turn = 'player' or 'enemy'."""
    player["combat_state"] = {
        "active":      True,
        "enemy_id":    enemy_id,
        "enemy_name":  enemy_data["name"],
        "enemy_hp":    enemy_data["hp"],
        "enemy_max_hp": enemy_data["max_hp"],
        "enemy_atk":   enemy_data["atk"],
        "enemy_def":   enemy_data["def"],
        "enemy_loot":  enemy_data.get("loot", []),
        "enemy_xp":    enemy_data.get("xp_reward", 0),
        "turn":        first_turn,
        "round":       1,
        "fled":        False,
    }
    return player

def _end_combat(player: dict, outcome: str, map_data: dict, location_key: str) -> dict:
    """Clean up combat state after victory, death, or flee."""
    cs = player.get("combat_state", {})

    if outcome == "victory":
        # Grant XP
        player["xp"] += cs.get("enemy_xp", 0)
        # Grant loot
        for item in cs.get("enemy_loot", []):
            player["inventory"].append(item)
        # Update milestones
        player["milestones"]["total_kills"] += 1
        enemy_id = cs.get("enemy_id", "")
        if enemy_id not in player["milestones"]["bosses_defeated"]:
            pass  # boss detection can be added later

        # Mark NPC as dead in map
        loc = map_data.get(location_key, {})
        if enemy_id in loc.get("npcs", {}):
            loc["npcs"][enemy_id]["status"] = "dead"
            loc["npcs"][enemy_id]["hp"]     = 0
            save_json("map.json", map_data)

        # Level up check
        if player["xp"] >= player["xp_to_next_level"]:
            player["level"]          += 1
            player["xp"]             -= player["xp_to_next_level"]
            player["xp_to_next_level"] = int(player["xp_to_next_level"] * 1.5)
            # Stat boosts on level up
            player["attributes"]["STR"] += 1
            player["attributes"]["CON"] += 1
            player["derived_stats"]["max_hp"] = 20 + player["attributes"]["CON"] * 5
            player["max_hp"] = player["derived_stats"]["max_hp"]

    player["combat_state"] = {"active": False}
    return player

def _handle_death(player: dict, saves: dict, player_id: str) -> dict:
    """Archive dead player to lineage, create descendant."""
    # Archive ancestor
    ancestor = {
        "name":     player["name"],
        "race":     player["race"],
        "class":    player["class"],
        "level":    player["level"],
        "killed_by": player.get("combat_state", {}).get("enemy_name", "unknown"),
        "history":  player["history"][-10:],
        "milestones": player["milestones"],
    }

    # Build descendant — inherits world memory, starts fresh
    descendant_name = f"{player['name']}'s Heir"
    descendant_id   = player_id + "_heir"

    world_state = load_json("world_state.json")
    race_data   = world_state["races"][player["race"]]
    class_data  = world_state["classes"][player["class"]]

    base = class_data["starting_attributes"]
    mods = race_data["stat_modifiers"]
    STR  = base["STR"] + mods.get("STR", 0)
    AGI  = base["AGI"] + mods.get("AGI", 0)
    CON  = base["CON"] + mods.get("CON", 0)
    ARC  = base["ARC"] + mods.get("ARC", 0)

    max_hp      = 20 + CON * 5
    max_stamina = 10
    max_mana    = ARC * 2

    skills = {
        skill_id: {"level": 1, "xp": 0, "modifications": []}
        for skill_id in class_data["starting_skills"]
    }

    descendant = {
        "name":           descendant_name,
        "race":           player["race"],
        "subrace":        None,
        "class":          player["class"],
        "subclass":       None,
        "status":         "alive",
        "history":        [f"I am the heir of {player['name']}, who fell in battle."],
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
        "lineage":    [ancestor] + player.get("lineage", []),
        "reputation": player.get("reputation", {"saltmarsh": 0, "ashen_ruins": 0, "void_wastes": 0}),
        "combat_state": {"active": False},
    }

    # Save descendant, remove dead player
    saves[descendant_id] = descendant
    del saves[player_id]
    save_json("saves.json", saves)

    return descendant, descendant_id, ancestor

# ── /register ──────────────────────────────────────────────────────────────────

@app.post("/register")
async def register(request: RegisterRequest):
    world_state = load_json("world_state.json")
    saves       = load_json("saves.json")

    if request.race not in world_state["races"]:
        raise HTTPException(status_code=400, detail=f"Unknown race: {request.race}")
    if request.player_class not in world_state["classes"]:
        raise HTTPException(status_code=400, detail=f"Unknown class: {request.player_class}")

    player_id = request.name.strip().lower().replace(" ", "_")

    if player_id in saves:
        return {"player_id": player_id, "state": _player_to_state(saves[player_id])}

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
        "lineage":      [],
        "reputation":   {"saltmarsh": 0, "ashen_ruins": 0, "void_wastes": 0},
        "combat_state": {"active": False},
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
    current_location = map_data.get(location_key, {})
    skill_defs       = world_state.get("skill_definitions", {})

    # ── Route to combat or exploration ────────────────────────────────────────
    cs = player.get("combat_state", {})

    if cs.get("active"):
        result = await _process_combat_turn(
            player, request.action, current_location,
            location_key, world_state, map_data, saves,
            request.player_id, skill_defs
        )
    else:
        result = await _process_exploration(
            player, request.action, current_location,
            location_key, world_state, map_data, saves,
            request.player_id, skill_defs
        )

    return result

# ── Exploration Handler ────────────────────────────────────────────────────────

async def _process_exploration(
    player, action, current_location, location_key,
    world_state, map_data, saves, player_id, skill_defs
):
    action_lower = action.lower()

    # Movement check
    for exit_key in current_location.get("exits", []):
        if exit_key.replace("_", " ") in action_lower or exit_key in action_lower:
            player["location"] = exit_key
            current_location   = map_data[exit_key]
            location_key       = exit_key
            break

    # Check if player is trying to attack an NPC → start combat
    npcs = current_location.get("npcs", {})
    combat_initiated = None
    first_turn       = "player"

    attack_keywords = ["attack", "fight", "kill", "stab", "strike", "hit", "punch", "charge", "ambush"]
    if any(kw in action_lower for kw in attack_keywords):
        for npc_id, npc_data in npcs.items():
            if npc_data.get("status") == "dead":
                continue
            npc_name_lower = npc_data["name"].lower()
            if any(word in action_lower for word in npc_name_lower.split()):
                combat_initiated = (npc_id, npc_data)
                # Player ambushes — they go first
                if "ambush" in action_lower or "sneak" in action_lower:
                    first_turn = "player"
                else:
                    first_turn = "player"
                break

    # Check if any hostile NPC auto-initiates combat (disposition <= -50)
    if not combat_initiated:
        for npc_id, npc_data in npcs.items():
            if npc_data.get("status") == "dead":
                continue
            if npc_data.get("disposition", 0) <= -50:
                combat_initiated = (npc_id, npc_data)
                first_turn       = "enemy"  # hostile NPCs ambush the player
                break

    if combat_initiated:
        npc_id, npc_data = combat_initiated
        player = _start_combat(player, npc_id, npc_data, first_turn)

        attrs = player["attributes"]
        cs    = player["combat_state"]

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
Then output EXACTLY these tags on new lines:
VISUAL: [scene description for image generation]"""

        narrative = "[Combat begins]"
        if client:
            response  = client.models.generate_content(model="gemini-2.5-flash", contents=combat_prompt)
            narrative = response.text

        display_text = "\n".join(
            line for line in narrative.splitlines()
            if not line.strip().startswith("VISUAL:")
        ).strip()

        player["history"].append(f"[COMBAT STARTED] vs {npc_data['name']}")
        player["history"] = player["history"][-20:]
        saves[player_id]  = player
        save_json("saves.json", saves)

        return {
            "text":         display_text,
            "image_base64": "",
            "status":       player["status"],
            "location":     current_location["name"],
            "state":        _player_to_state(player),
            "combat_event": "start",
        }

    # Normal exploration
    player["history"].append(action)
    player["history"] = player["history"][-20:]

    attrs = player["attributes"]
    prompt = f"""You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

WORLD HISTORY: {world_state['world_history']}
LOCATION: {current_location['name']}
DESCRIPTION: {current_location['description']}
LOCATION STATE: {current_location.get('state', {})}
NPCS PRESENT: {[f"{k}: {v['name']} (disposition: {v.get('disposition',0)}, status: {v.get('status','alive')})" for k,v in current_location.get('npcs',{}).items()]}
LOCATION HISTORY: {current_location.get('history', [])[-5:]}

PLAYER: {player['name']} | Race: {player['race']} | Class: {player['class']}
HP: {player['hp']}/{player['max_hp']} | Level: {player['level']}
STR:{attrs['STR']} AGI:{attrs['AGI']} CON:{attrs['CON']} ARC:{attrs['ARC']}
SKILLS: {list(player['skills'].keys())}
INVENTORY: {player['inventory']}
RECENT ACTIONS: {player['history'][-5:]}

PLAYER ACTION: {action}

Respond with vivid narrative (2-3 sentences). Then on a new line:
VISUAL: [one sentence describing the scene for image generation]"""

    narrative = "[The void is silent — no AI connected]"
    if client:
        response  = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        narrative = response.text

    display_text = "\n".join(
        line for line in narrative.splitlines()
        if not line.strip().startswith("VISUAL:")
    ).strip()

    saves[player_id] = player
    save_json("saves.json", saves)

    return {
        "text":         display_text,
        "image_base64": "",
        "status":       player["status"],
        "location":     current_location["name"],
        "state":        _player_to_state(player),
    }

# ── Combat Turn Handler ────────────────────────────────────────────────────────

async def _process_combat_turn(
    player, action, current_location, location_key,
    world_state, map_data, saves, player_id, skill_defs
):
    cs    = player["combat_state"]
    attrs = player["attributes"]

    # Detect skill usage
    skill_used = None
    for skill_id in player["skills"].keys():
        skill_name = skill_defs.get(skill_id, {}).get("name", skill_id).lower()
        if skill_id.replace("_", " ") in action.lower() or skill_name in action.lower():
            skill_used = skill_id
            break

    # Detect flee attempt
    flee_attempt = any(w in action.lower() for w in ["flee", "run", "escape", "retreat", "flee"])

    # Calculate damage ranges
    p_min, p_max = _calc_player_damage_range(player, skill_used, skill_defs)
    e_min, e_max = _calc_enemy_damage_range(
        {"atk": cs["enemy_atk"]}, player["derived_stats"]["def"]
    )

    # Speed / turn order — AGI + d6
    player_speed = attrs["AGI"] + random.randint(1, 6)
    enemy_speed  = random.randint(1, 8)  # enemies have flat speed pool
    player_first = cs["turn"] == "player" or player_speed >= enemy_speed

    # Build combat prompt
    skill_info = ""
    if skill_used and skill_used in skill_defs:
        sd = skill_defs[skill_used]
        skill_info = f"SKILL USED: {sd['name']} — {sd['description']} | base_dmg: {sd['base_damage']} effect: {sd['effect']}"

    combat_prompt = f"""You are a dark fantasy dungeon master for 'Echoes of the Fallen'.
This is ROUND {cs['round']} of combat.

LOCATION: {current_location['name']}

PLAYER: {player['name']} | {player['race']} {player['class']}
HP: {player['hp']}/{player['max_hp']} | Stamina: {player['stamina']}/{player['max_stamina']} | Mana: {player['mana']}/{player['max_mana']}
STR:{attrs['STR']} AGI:{attrs['AGI']} CON:{attrs['CON']} ARC:{attrs['ARC']}
PLAYER DAMAGE RANGE THIS TURN: {p_min} to {p_max}
{skill_info}

ENEMY: {cs['enemy_name']}
HP: {cs['enemy_hp']}/{cs['enemy_max_hp']} | ATK: {cs['enemy_atk']} DEF: {cs['enemy_def']}
ENEMY DAMAGE RANGE THIS TURN: {e_min} to {e_max}

PLAYER ACTION: {action}
FLEE ATTEMPT: {flee_attempt}
PLAYER GOES FIRST: {player_first}

Narrate this combat round vividly (3-4 sentences). Be specific about what happens.
Then output EXACTLY these tags on separate lines — no extra text on these lines:
PLAYER_DAMAGE: [integer between {p_min} and {p_max}, or 0 if player missed/fled]
ENEMY_DAMAGE: [integer between {e_min} and {e_max}, or 0 if enemy missed or player fled successfully]
SKILL_USED: [skill_id or none]
FLEE_OUTCOME: [none / success / fail / captured]
VISUAL: [one sentence describing the combat scene]"""

    narrative = "[Combat continues]"
    raw_text  = ""
    if client:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=combat_prompt)
        raw_text = response.text
        narrative = raw_text

    # Parse Gemini tags
    def parse_tag(tag, text, default):
        for line in text.splitlines():
            if line.strip().startswith(f"{tag}:"):
                val = line.split(":", 1)[1].strip()
                return val
        return default

    try:
        player_dmg   = int(parse_tag("PLAYER_DAMAGE", raw_text, str(random.randint(p_min, p_max))))
    except ValueError:
        player_dmg   = random.randint(p_min, p_max)

    try:
        enemy_dmg    = int(parse_tag("ENEMY_DAMAGE",  raw_text, str(random.randint(e_min, e_max))))
    except ValueError:
        enemy_dmg    = random.randint(e_min, e_max)

    flee_outcome     = parse_tag("FLEE_OUTCOME", raw_text, "none").lower()

    # Strip tags from display text
    tag_prefixes = ["PLAYER_DAMAGE:", "ENEMY_DAMAGE:", "SKILL_USED:", "FLEE_OUTCOME:", "VISUAL:"]
    display_text = "\n".join(
        line for line in narrative.splitlines()
        if not any(line.strip().startswith(t) for t in tag_prefixes)
    ).strip()

    # ── Apply combat results ───────────────────────────────────────────────────
    combat_event = "ongoing"
    extra_data   = {}

    if flee_outcome == "success":
        # Successful flee — move to a random exit
        exits = current_location.get("exits", [])
        if exits:
            player["location"] = random.choice(exits)
        player  = _end_combat(player, "fled", map_data, location_key)
        combat_event = "fled"

    elif flee_outcome == "captured":
        player["hp"]    = max(1, player["hp"] - enemy_dmg)
        player["status"] = "captured"
        player  = _end_combat(player, "captured", map_data, location_key)
        combat_event = "captured"

    elif flee_outcome == "fail":
        # Failed flee — take enemy damage and combat continues
        player["hp"] = max(0, player["hp"] - enemy_dmg)
        player["milestones"]["total_damage_absorbed"] += enemy_dmg
        cs["round"] += 1

    else:
        # Normal combat exchange
        if player_first:
            # Player attacks first
            cs["enemy_hp"] = max(0, cs["enemy_hp"] - player_dmg)
            player["milestones"]["total_damage_dealt"] += player_dmg

            if cs["enemy_hp"] <= 0:
                combat_event = "victory"
                player = _end_combat(player, "victory", map_data, location_key)
            else:
                # Enemy counter-attacks
                player["hp"] = max(0, player["hp"] - enemy_dmg)
                player["milestones"]["total_damage_absorbed"] += enemy_dmg
                cs["round"] += 1
        else:
            # Enemy attacks first
            player["hp"] = max(0, player["hp"] - enemy_dmg)
            player["milestones"]["total_damage_absorbed"] += enemy_dmg

            if player["hp"] <= 0:
                combat_event = "death"
            else:
                cs["enemy_hp"] = max(0, cs["enemy_hp"] - player_dmg)
                player["milestones"]["total_damage_dealt"] += player_dmg

                if cs["enemy_hp"] <= 0:
                    combat_event = "victory"
                    player = _end_combat(player, "victory", map_data, location_key)
                else:
                    cs["round"] += 1

        # Nearly died milestone
        if player["hp"] <= player["max_hp"] * 0.25 and player["hp"] > 0:
            player["milestones"]["times_nearly_died"] += 1

    # ── Death handling ─────────────────────────────────────────────────────────
    if combat_event == "death" or player["hp"] <= 0:
        player["status"] = "dead"
        player["hp"]     = 0
        combat_event     = "death"

        descendant, descendant_id, ancestor = _handle_death(player, saves, player_id)
        extra_data = {
            "ancestor":      ancestor,
            "descendant_id": descendant_id,
        }
        player = descendant

    # ── Save & return ──────────────────────────────────────────────────────────
    player["history"].append(f"[COMBAT R{cs.get('round',1)}] {action}")
    player["history"] = player["history"][-20:]

    current_location_name = map_data.get(player["location"], current_location).get("name", player["location"])

    saves[player_id] = player
    save_json("saves.json", saves)

    return {
        "text":         display_text,
        "image_base64": "",
        "status":       player["status"],
        "location":     current_location_name,
        "state":        _player_to_state(player),
        "combat_event": combat_event,
        **extra_data,
    }

# ── State Serializer ───────────────────────────────────────────────────────────

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
        "combat_state":     player.get("combat_state", {"active": False}),
    }

# ── /levelup (Trevor's Feature) ────────────────────────────────────────────────
@app.post("/levelup")
async def process_levelup(request: LevelUpRequest):
    saves = load_json("saves.json")
    player = saves.get(request.player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if player["xp"] < player["xp_to_next_level"]:
        raise HTTPException(status_code=400, detail="Not enough XP to level up.")

    stat = request.stat_to_increase.upper()
    if stat in player["attributes"]:
        # 1. Increase the chosen stat
        player["attributes"][stat] += 1
        
        # 2. Consume XP and scale the next level requirement
        player["level"] += 1
        player["xp"] -= player["xp_to_next_level"]
        player["xp_to_next_level"] = int(player["xp_to_next_level"] * 1.5)
        
        # 3. Recalculate max HP and give them a free heal!
        player["max_hp"] = 20 + (player["attributes"]["CON"] * 5)
        player["hp"] = player["max_hp"]

        # Save to disk
        saves[request.player_id] = player
        save_json("saves.json", saves)

        return {"message": "Ascension complete.", "state": _player_to_state(player)}
    else:
        raise HTTPException(status_code=400, detail="Invalid stat selected.")