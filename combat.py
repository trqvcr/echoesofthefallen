import random
import time
from typing import Optional

from db import get_world, save_player, save_location
from images import generate_scene_image


# ── Damage Calculators ─────────────────────────────────────────────────────────

def _calc_player_damage_range(player: dict, skill_id: Optional[str], skill_defs: dict) -> tuple:
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
    raw_min = max(0, enemy["atk"] - player_def - 1)
    raw_max = max(1, enemy["atk"] - player_def + 2)
    return (raw_min, raw_max)


# ── Combat State Management ────────────────────────────────────────────────────

def _start_combat(player: dict, enemy_id: str, enemy_data: dict, first_turn: str) -> dict:
    player["combat_state"] = {
        "active":       True,
        "enemy_id":     enemy_id,
        "enemy_name":   enemy_data["name"],
        "enemy_hp":     enemy_data["hp"],
        "enemy_max_hp": enemy_data["max_hp"],
        "enemy_atk":    enemy_data["atk"],
        "enemy_def":    enemy_data["def"],
        "enemy_loot":   enemy_data.get("loot", []),
        "enemy_xp":     enemy_data.get("xp_reward", 0),
        "turn":         first_turn,
        "round":        1,
        "fled":         False,
    }
    return player


def _end_combat(player: dict, outcome: str, all_locations: dict, location_key: str) -> dict:
    cs = player.get("combat_state", {})

    if outcome == "victory":
        player["xp"] += cs.get("enemy_xp", 0)
        for item in cs.get("enemy_loot", []):
            player["inventory"].append(item)
        player["milestones"]["total_kills"] += 1

        enemy_id = cs.get("enemy_id", "")
        loc = all_locations.get(location_key, {})
        if enemy_id in loc.get("npcs", {}):
            loc["npcs"][enemy_id]["status"]  = "dead"
            loc["npcs"][enemy_id]["hp"]      = 0
            loc["npcs"][enemy_id]["died_at"] = time.time()
            save_location(location_key, loc)

        if enemy_id not in player["milestones"]["bosses_defeated"]:
            player["milestones"]["bosses_defeated"].append(enemy_id)

        if player["xp"] >= player["xp_to_next_level"]:
            player["level"]            += 1
            player["xp"]               -= player["xp_to_next_level"]
            player["xp_to_next_level"]  = int(player["xp_to_next_level"] * 1.5)
            player["attributes"]["STR"] += 1
            player["attributes"]["AGI"] += 1
            player["attributes"]["CON"] += 1
            player["attributes"]["ARC"] += 1
            attrs = player["attributes"]
            player["derived_stats"]["max_hp"]       = 20 + attrs["CON"] * 5
            player["derived_stats"]["atk"]          = attrs["STR"] + 2
            player["derived_stats"]["def"]          = attrs["CON"] // 2
            player["derived_stats"]["dodge_chance"] = attrs["AGI"] * 2
            player["max_hp"]   = player["derived_stats"]["max_hp"]
            player["max_mana"] = attrs["ARC"] * 2

    player["combat_state"] = {"active": False}
    return player


def _make_ancestor_record(player: dict) -> dict:
    return {
        "name":       player["name"],
        "race":       player["race"],
        "class":      player["class"],
        "level":      player["level"],
        "killed_by":  player.get("combat_state", {}).get("enemy_name", "unknown"),
        "history":    player["history"][-10:],
        "milestones": player["milestones"],
    }


def build_heir(dead_player: dict, heir_name: str) -> dict:
    world_state = get_world()
    race_data   = world_state["races"][dead_player["race"]]
    class_data  = world_state["classes"][dead_player["class"]]

    base = class_data["starting_attributes"]
    mods = race_data["stat_modifiers"]
    STR  = base["STR"] + mods.get("STR", 0)
    AGI  = base["AGI"] + mods.get("AGI", 0)
    CON  = base["CON"] + mods.get("CON", 0)
    ARC  = base["ARC"] + mods.get("ARC", 0)

    max_hp      = 20 + CON * 5
    max_stamina = 10
    max_mana    = ARC * 2
    generation  = len(dead_player.get("lineage", [])) + 2

    skills = {
        skill_id: {"level": 1, "xp": 0, "modifications": []}
        for skill_id in class_data["starting_skills"]
    }

    ancestor = _make_ancestor_record(dead_player)

    return {
        "name":             f"{heir_name}, Heir of {dead_player['name'].split(', Heir of')[0]}",
        "password_hash":    dead_player.get("password_hash", ""),
        "race":             dead_player["race"],
        "subrace":          None,
        "class":            dead_player["class"],
        "subclass":         None,
        "status":           "alive",
        "history":          [f"Generation {generation}. {heir_name} rises from the ashes of {dead_player['name']}."],
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
        "lineage":          [ancestor] + dead_player.get("lineage", []),
        "reputation":       dead_player.get("reputation", {"saltmarsh": 0, "ashen_ruins": 0, "void_wastes": 0}),
        "combat_state":     {"active": False},
        "visited_locations": ["ashen_courtyard"],
    }


# ── Player State Serializer ────────────────────────────────────────────────────

def _ensure_location_visited(player: dict) -> list:
    """Return visited_locations, always including current location."""
    visited = list(player.get("visited_locations", []))
    current = player.get("location", "ashen_courtyard")
    if current not in visited:
        visited.append(current)
    return visited


def player_to_state(player: dict, player_id: str = None) -> dict:
    attrs = player.get("attributes", {})
    if player_id is None:
        player_id = player["name"].lower().replace(" ", "_")
    return {
        "house_name":       player["name"],
        "player_id":        player_id,
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
        "combat_state":        player.get("combat_state", {"active": False}),
        "avatar_description":  player.get("avatar_description", ""),
        "avatar_portrait":     player.get("avatar_portrait", ""),
        "visited_locations":   _ensure_location_visited(player),
    }


# ── Combat Turn Handler ────────────────────────────────────────────────────────

async def process_combat_turn(
    player, action, current_location, location_key,
    world_state, all_locations, player_id, skill_defs, client
) -> dict:
    cs    = player["combat_state"]
    attrs = player["attributes"]

    skill_used = None
    for skill_id in player["skills"].keys():
        skill_name = skill_defs.get(skill_id, {}).get("name", skill_id).lower()
        if skill_id.replace("_", " ") in action.lower() or skill_name in action.lower():
            skill_used = skill_id
            break

    if skill_used and skill_used in player["skills"]:
        player["skills"][skill_used]["xp"] += 1
        if player["skills"][skill_used]["xp"] >= 10 * player["skills"][skill_used]["level"]:
            player["skills"][skill_used]["xp"]    = 0
            player["skills"][skill_used]["level"] += 1

    flee_attempt = any(w in action.lower() for w in ["flee", "run", "escape", "retreat"])

    p_min, p_max = _calc_player_damage_range(player, skill_used, skill_defs)
    e_min, e_max = _calc_enemy_damage_range({"atk": cs["enemy_atk"]}, player["derived_stats"]["def"])

    player_speed = attrs.get("AGI", 0) + random.randint(1, 6)
    enemy_speed  = random.randint(1, 8)
    player_first = cs["turn"] == "player" or player_speed >= enemy_speed

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
Then output EXACTLY these tags on separate lines:
PLAYER_DAMAGE: [integer — scale by action effectiveness. Normal attack = {p_min}-{p_max}. Weak/silly actions (tickle, poke, slap, gentle push) = 1 to {max(1, p_min//2)}. Powerful/skilled strike = up to {p_max + 3}. Miss or fled = 0]
ENEMY_DAMAGE: [integer between {e_min} and {e_max}, or 0 if enemy missed or player fled successfully]
SKILL_USED: [skill_id or none]
FLEE_OUTCOME: [none / success / fail / captured]
VISUAL: [one sentence describing the combat scene]"""

    narrative = "[Combat continues]"
    raw_text  = ""
    if client:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=combat_prompt)
        raw_text = response.text or ""
        narrative = raw_text or "[Combat continues]"

    def parse_tag(tag, text, default=""):
        for line in text.splitlines():
            if line.strip().startswith(f"{tag}:"):
                return line.split(":", 1)[1].strip()
        return default

    try:
        player_dmg = max(0, int(parse_tag("PLAYER_DAMAGE", raw_text, str(random.randint(p_min, p_max)))))
    except ValueError:
        player_dmg = random.randint(p_min, p_max)

    try:
        enemy_dmg = int(parse_tag("ENEMY_DAMAGE", raw_text, str(random.randint(e_min, e_max))))
    except ValueError:
        enemy_dmg = random.randint(e_min, e_max)

    flee_outcome = parse_tag("FLEE_OUTCOME", raw_text, "none").lower()

    tag_prefixes = ["PLAYER_DAMAGE:", "ENEMY_DAMAGE:", "SKILL_USED:", "FLEE_OUTCOME:", "VISUAL:"]
    display_text = "\n".join(
        line for line in narrative.splitlines()
        if not any(line.strip().startswith(t) for t in tag_prefixes)
    ).strip()

    # ── Apply results ──────────────────────────────────────────────────────────
    combat_event = "ongoing"
    extra_data   = {}

    if flee_outcome == "success":
        exits = current_location.get("exits", [])
        if exits:
            player["location"] = random.choice(exits)
        player       = _end_combat(player, "fled", all_locations, location_key)
        combat_event = "fled"

    elif flee_outcome == "captured":
        player["hp"]     = max(1, player["hp"] - enemy_dmg)
        player["status"] = "captured"
        player           = _end_combat(player, "captured", all_locations, location_key)
        combat_event     = "captured"

    elif flee_outcome == "fail":
        player["hp"] = max(0, player["hp"] - enemy_dmg)
        player["milestones"]["total_damage_absorbed"] += enemy_dmg
        cs["round"] += 1

    else:
        if player_first:
            cs["enemy_hp"] = max(0, cs["enemy_hp"] - player_dmg)
            player["milestones"]["total_damage_dealt"] += player_dmg
            if cs["enemy_hp"] <= 0:
                combat_event = "victory"
                player = _end_combat(player, "victory", all_locations, location_key)
            else:
                player["hp"] = max(0, player["hp"] - enemy_dmg)
                player["milestones"]["total_damage_absorbed"] += enemy_dmg
                cs["round"] += 1
        else:
            player["hp"] = max(0, player["hp"] - enemy_dmg)
            player["milestones"]["total_damage_absorbed"] += enemy_dmg
            if player["hp"] <= 0:
                combat_event = "death"
            else:
                cs["enemy_hp"] = max(0, cs["enemy_hp"] - player_dmg)
                player["milestones"]["total_damage_dealt"] += player_dmg
                if cs["enemy_hp"] <= 0:
                    combat_event = "victory"
                    player = _end_combat(player, "victory", all_locations, location_key)
                else:
                    cs["round"] += 1

        if player["hp"] <= player["max_hp"] * 0.25 and player["hp"] > 0:
            player["milestones"]["times_nearly_died"] += 1

    # ── Death ──────────────────────────────────────────────────────────────────
    if combat_event == "death" or player["hp"] <= 0:
        player["status"] = "dead"
        player["hp"]     = 0
        combat_event     = "death"
        player["history"].append(f"[COMBAT R{cs.get('round',1)}] {action}")
        player["history"] = player["history"][-20:]
        save_player(player_id, player)
        extra_data = {"ancestor": _make_ancestor_record(player), "player_id": player_id}
    else:
        player["history"].append(f"[COMBAT R{cs.get('round',1)}] {action}")
        player["history"] = player["history"][-20:]
        save_player(player_id, player)

    current_location_name = all_locations.get(player["location"], current_location).get("name", player["location"])

    return {
        "text":         display_text,
        "image_base64": generate_scene_image(client, parse_tag("VISUAL", raw_text), player.get("avatar_description", "")),
        "status":       player["status"],
        "location":     current_location_name,
        "state":        player_to_state(player, player_id),
        "combat_event": combat_event,
        "player_dmg":   player_dmg if flee_outcome not in ("success", "captured") else 0,
        "enemy_dmg":    enemy_dmg  if flee_outcome not in ("success",)            else 0,
        **extra_data,
    }
