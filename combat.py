import random
import time
from typing import Optional

from db import get_world, save_player, save_location
from images import generate_scene_image, generate_npc_portrait


# ── Skill Definition Resolver ──────────────────────────────────────────────────

def _resolve_all_skill_defs(world_skill_defs: dict, player_skills: dict) -> dict:
    """Merge world skill defs with any player-side overrides (forged/custom skills)."""
    merged = dict(world_skill_defs)
    for sid, sdata in player_skills.items():
        if sdata.get("forged") or sdata.get("custom"):
            merged[sid] = sdata
    return merged


# ── Status Effect Helpers ──────────────────────────────────────────────────────

def _sum_effect(effects: list, effect_type: str) -> int:
    """Sum the value of all active effects of a given type."""
    return sum(e["value"] for e in effects if e["type"] == effect_type)


def _has_effect(effects: list, effect_type: str) -> bool:
    return any(e["type"] == effect_type for e in effects)


def _add_effect(effects: list, effect_type: str, value: int, duration: int) -> list:
    """Add or refresh an effect. Replaces existing effect of same type if present."""
    effects = [e for e in effects if e["type"] != effect_type]
    if duration > 0:
        effects.append({"type": effect_type, "value": value, "turns_remaining": duration})
    return effects


def _tick_effects(effects: list) -> list:
    """Decrement all durations and remove expired effects."""
    ticked = []
    for e in effects:
        remaining = e["turns_remaining"] - 1
        if remaining > 0:
            ticked.append({**e, "turns_remaining": remaining})
    return ticked


# ── Damage Calculators ─────────────────────────────────────────────────────────

def _calc_player_damage_range(player: dict, skill_id: Optional[str], skill_defs: dict) -> tuple:
    attrs    = player["attributes"]
    base_atk = player["derived_stats"]["atk"]

    if skill_id and skill_id in skill_defs:
        skill     = skill_defs[skill_id]
        base_dmg  = skill.get("base_damage", 0)
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

        # Grant forge charge for boss kills (enemies with xp_reward >= 20)
        if cs.get("enemy_xp", 0) >= 20:
            player["forge_charges"] = player.get("forge_charges", 0) + 1

        if enemy_id not in player["milestones"]["bosses_defeated"]:
            player["milestones"]["bosses_defeated"].append(enemy_id)

        # Level up
        while player["xp"] >= player["xp_to_next_level"]:
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
            player["max_hp"]    = player["derived_stats"]["max_hp"]
            player["max_mana"]  = attrs["ARC"] * 2
            # Restore resources on level up
            player["stamina"]   = player["max_stamina"]
            player["mana"]      = player["max_mana"]

            # Every 3 levels offer a skill choice from advanced pool
            if player["level"] % 3 == 0 and not player.get("pending_skill_offer"):
                try:
                    world_state  = get_world()
                    pools        = world_state.get("class_skill_pools", {})
                    class_pool   = pools.get(player["class"], {})
                    advanced     = class_pool.get("advanced", [])
                    owned        = set(player.get("skills", {}).keys())
                    available    = [s for s in advanced if s not in owned]
                    if available:
                        offer = random.sample(available, min(3, len(available)))
                        player["pending_skill_offer"] = offer
                except Exception:
                    pass

    # Restore some stamina after combat
    player["stamina"] = min(player["max_stamina"], player.get("stamina", 0) + 3)
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
        "combat_state":      {"active": False},
        "visited_locations": ["ashen_courtyard"],
        "travel_progress":   {},
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
        player_id = player.get("name", "unknown").lower().replace(" ", "_")
    con = attrs.get("CON", 0)
    arc = attrs.get("ARC", 0)
    return {
        "house_name":       player.get("name", ""),
        "player_id":        player_id,
        "race":             player.get("race", ""),
        "class":            player.get("class", ""),
        "status":           player.get("status", "alive"),
        "location":         player.get("location", "ashen_courtyard"),
        "hp":               player.get("hp", 20 + con * 5),
        "max_hp":           player.get("max_hp", 20 + con * 5),
        "stamina":          player.get("stamina", 10),
        "max_stamina":      player.get("max_stamina", 10),
        "mana":             player.get("mana", arc * 2),
        "max_mana":         player.get("max_mana", arc * 2),
        "level":            player.get("level", 1),
        "xp":               player.get("xp", 0),
        "xp_to_next_level": player.get("xp_to_next_level", 100),
        "str":              attrs.get("STR", 0),
        "agi":              attrs.get("AGI", 0),
        "con":              con,
        "arc":              arc,
        "inventory":        player.get("inventory", []),
        "equipped":         player.get("equipped", {}),
        "skills":           player.get("skills", {}),
        "milestones":       player.get("milestones", {}),
        "lineage":          player.get("lineage", []),
        "reputation":       player.get("reputation", {}),
        "combat_state":        player.get("combat_state", {"active": False}),
        "avatar_description":  player.get("avatar_description", ""),
        "avatar_portrait":     player.get("avatar_portrait", ""),
        "visited_locations":    _ensure_location_visited(player),
        "travel_progress":      player.get("travel_progress", {}),
        "forge_charges":        player.get("forge_charges", 0),
        "pending_skill_offer":  player.get("pending_skill_offer", None),
    }


# ── Combat Turn Handler ────────────────────────────────────────────────────────

async def process_combat_turn(
    player, action, current_location, location_key,
    world_state, all_locations, player_id, skill_defs, client
) -> dict:
    cs    = player["combat_state"]
    attrs = player["attributes"]

    # Ensure status effect containers exist
    cs.setdefault("player_effects", [])
    cs.setdefault("enemy_effects",  [])
    cs.setdefault("skill_cooldowns", {})

    # ── Tick DoT effects at round start ───────────────────────────────────────
    dot_damage = sum(
        e["value"] for e in cs["enemy_effects"]
        if e["type"] in ("poison", "bleed")
    )
    if dot_damage:
        cs["enemy_hp"] = max(0, cs["enemy_hp"] - dot_damage)

    # Early victory from DoT
    if cs["enemy_hp"] <= 0:
        victory_loot = list(cs.get("enemy_loot", []))
        victory_xp   = cs.get("enemy_xp", 0)
        player = _end_combat(player, "victory", all_locations, location_key)
        save_player(player_id, player)
        dot_msg = f"The poison does its work. {cs.get('enemy_name','The enemy')} collapses."
        return {
            "text": dot_msg, "image_base64": "", "npc_portrait": "",
            "status": player["status"],
            "location": current_location.get("name", location_key),
            "state": player_to_state(player, player_id),
            "combat_event": "victory",
            "player_dmg": dot_damage, "enemy_dmg": 0,
            "victory_loot": victory_loot, "victory_xp": victory_xp,
        }

    all_skill_defs = _resolve_all_skill_defs(skill_defs, player.get("skills", {}))

    # ── Skill detection ───────────────────────────────────────────────────────
    skill_used          = None
    skill_blocked_msg   = ""
    for skill_id in player["skills"].keys():
        sdef       = all_skill_defs.get(skill_id, {})
        skill_name = sdef.get("name", skill_id).lower()
        if skill_id.replace("_", " ") in action.lower() or skill_name in action.lower():
            skill_used = skill_id
            break

    if skill_used:
        cd = cs["skill_cooldowns"].get(skill_used, 0)
        if cd > 0:
            skill_blocked_msg = f"({all_skill_defs[skill_used].get('name', skill_used)} on cooldown: {cd} turns)"
            skill_used = None
        else:
            sdef         = all_skill_defs.get(skill_used, {})
            mana_cost    = sdef.get("mana_cost", 0)
            stamina_cost = sdef.get("stamina_cost", 0)
            if player["mana"] < mana_cost:
                skill_blocked_msg = f"(Not enough mana for {sdef.get('name','skill')}: need {mana_cost})"
                skill_used = None
            elif player["stamina"] < stamina_cost:
                skill_blocked_msg = f"(Not enough stamina for {sdef.get('name','skill')}: need {stamina_cost})"
                skill_used = None

    if skill_used:
        sdef = all_skill_defs[skill_used]
        player["mana"]    = max(0, player["mana"]    - sdef.get("mana_cost", 0))
        player["stamina"] = max(0, player["stamina"] - sdef.get("stamina_cost", 0))
        player["skills"][skill_used]["xp"] += 1
        if player["skills"][skill_used]["xp"] >= 10 * player["skills"][skill_used]["level"]:
            player["skills"][skill_used]["xp"]    = 0
            player["skills"][skill_used]["level"] += 1
        cs["skill_cooldowns"][skill_used] = sdef.get("cooldown_turns", 0)

    flee_attempt = any(w in action.lower() for w in ["flee", "run", "escape", "retreat"])

    self_harm = any(w in action.lower() for w in [
        "kill myself", "kill my self", "suicide", "end my life",
        "slay myself", "slit my throat", "stab myself", "end it",
    ])
    if self_harm:
        player["hp"]     = 0
        player["status"] = "dead"
        player["history"].append(f"[COMBAT R{cs.get('round',1)}] {action}")
        player["history"] = player["history"][-20:]
        save_player(player_id, player)
        return {
            "text": f"{player['name']} chose death over defeat. The void claims another soul.",
            "image_base64": "", "status": "dead",
            "location": current_location.get("name", location_key),
            "state": player_to_state(player, player_id),
            "combat_event": "death", "player_dmg": 0, "enemy_dmg": 0,
            "ancestor": _make_ancestor_record(player), "player_id": player_id,
        }

    # ── Gather active effect modifiers ────────────────────────────────────────
    enemy_atk_eff  = max(1, cs["enemy_atk"] - _sum_effect(cs["enemy_effects"], "weaken"))
    enemy_stunned  = _has_effect(cs["enemy_effects"], "stun")
    player_crit    = _sum_effect(cs["player_effects"], "crit")
    player_expose  = _sum_effect(cs["player_effects"], "expose")
    player_dodge_b = _sum_effect(cs["player_effects"], "dodge")
    player_block   = _sum_effect(cs["player_effects"], "block")   # % reduction
    player_shield  = _sum_effect(cs["player_effects"], "shield")  # flat absorb

    p_min, p_max = _calc_player_damage_range(player, skill_used, all_skill_defs)
    p_max_eff    = p_max + player_crit + player_expose

    e_min, e_max = _calc_enemy_damage_range({"atk": enemy_atk_eff}, player["derived_stats"]["def"])
    if enemy_stunned:
        e_min, e_max = 0, 0

    player_speed = attrs.get("AGI", 0) + random.randint(1, 6) + (player_dodge_b // 10)
    enemy_speed  = random.randint(1, 8)
    player_first = cs["turn"] == "player" or player_speed >= enemy_speed

    # ── Build Gemini prompt ───────────────────────────────────────────────────
    skill_info = ""
    if skill_used:
        sd = all_skill_defs[skill_used]
        skill_info = (
            f"SKILL USED: {sd['name']} — {sd['description']}\n"
            f"  base_dmg: {sd.get('base_damage',0)} | effect: {sd.get('effect','none')} "
            f"(value: {sd.get('effect_value',0)}, duration: {sd.get('effect_duration',0)} turns)\n"
            f"  cost: {sd.get('mana_cost',0)} mana / {sd.get('stamina_cost',0)} stamina"
        )
    if skill_blocked_msg:
        skill_info += f"\nSKILL BLOCKED: {skill_blocked_msg} — player attacks normally instead."

    active_effects_str = ""
    if cs["player_effects"]:
        active_effects_str += "PLAYER ACTIVE EFFECTS: " + ", ".join(
            f"{e['type']}({e['turns_remaining']}t)" for e in cs["player_effects"]
        ) + "\n"
    if cs["enemy_effects"]:
        active_effects_str += "ENEMY ACTIVE EFFECTS: " + ", ".join(
            f"{e['type']}({e['turns_remaining']}t)" for e in cs["enemy_effects"]
        ) + "\n"
    if dot_damage:
        active_effects_str += f"POISON/BLEED DEALT {dot_damage} damage to enemy this round.\n"
    if enemy_stunned:
        active_effects_str += "ENEMY IS STUNNED — cannot act this round.\n"

    combat_prompt = f"""You are a dark fantasy dungeon master for 'Echoes of the Fallen'.
This is ROUND {cs['round']} of combat.

LOCATION: {current_location['name']}

PLAYER: {player['name']} | {player['race']} {player['class']}
HP: {player['hp']}/{player['max_hp']} | Stamina: {player['stamina']}/{player['max_stamina']} | Mana: {player['mana']}/{player['max_mana']}
STR:{attrs['STR']} AGI:{attrs['AGI']} CON:{attrs['CON']} ARC:{attrs['ARC']}
PLAYER DAMAGE RANGE THIS TURN: {p_min} to {p_max_eff}
{skill_info}

ENEMY: {cs['enemy_name']}
HP: {cs['enemy_hp']}/{cs['enemy_max_hp']} | ATK: {enemy_atk_eff} DEF: {cs['enemy_def']}
ENEMY DAMAGE RANGE THIS TURN: {e_min} to {e_max}

{active_effects_str}
PLAYER ACTION: {action}
FLEE ATTEMPT: {flee_attempt}
PLAYER GOES FIRST: {player_first}

Narrate this combat round vividly (3-4 sentences). Reflect any active effects in the narration.
Then output EXACTLY these tags on separate lines:
PLAYER_DAMAGE: [integer — normal = {p_min}-{p_max_eff}. Weak/silly = 1 to {max(1,p_min//2)}. Miss or fled = 0]
ENEMY_DAMAGE: [integer {e_min}-{e_max}, or 0 if stunned/missed/fled]
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
        player_dmg = max(0, int(parse_tag("PLAYER_DAMAGE", raw_text, str(random.randint(p_min, p_max_eff)))))
    except ValueError:
        player_dmg = random.randint(p_min, p_max_eff)

    try:
        enemy_dmg = int(parse_tag("ENEMY_DAMAGE", raw_text, str(random.randint(e_min, e_max) if not enemy_stunned else 0)))
    except ValueError:
        enemy_dmg = 0 if enemy_stunned else random.randint(e_min, e_max)

    if enemy_stunned:
        enemy_dmg = 0

    flee_outcome = parse_tag("FLEE_OUTCOME", raw_text, "none").lower()

    tag_prefixes = ["PLAYER_DAMAGE:", "ENEMY_DAMAGE:", "SKILL_USED:", "FLEE_OUTCOME:", "VISUAL:"]
    display_text = "\n".join(
        line for line in narrative.splitlines()
        if not any(line.strip().startswith(t) for t in tag_prefixes)
    ).strip()

    # ── Apply new skill effect ────────────────────────────────────────────────
    if skill_used:
        sdef        = all_skill_defs[skill_used]
        effect      = sdef.get("effect", "none")
        eff_val     = sdef.get("effect_value", 0)
        eff_dur     = sdef.get("effect_duration", 0)
        if effect != "none" and eff_dur > 0:
            if effect in ("poison", "bleed", "stun", "weaken"):
                cs["enemy_effects"] = _add_effect(cs["enemy_effects"], effect, eff_val, eff_dur)
            elif effect in ("block", "dodge", "shield", "crit", "expose"):
                cs["player_effects"] = _add_effect(cs["player_effects"], effect, eff_val, eff_dur)

    # ── Apply damage reduction from player effects ────────────────────────────
    if player_block > 0 and enemy_dmg > 0:
        enemy_dmg = max(0, int(enemy_dmg * (1 - player_block / 100)))
        cs["player_effects"] = [e for e in cs["player_effects"] if e["type"] != "block"]

    if player_shield > 0 and enemy_dmg > 0:
        absorbed   = min(player_shield, enemy_dmg)
        enemy_dmg -= absorbed
        remaining  = player_shield - absorbed
        cs["player_effects"] = [
            ({**e, "value": remaining} if e["type"] == "shield" and remaining > 0 else None)
            for e in cs["player_effects"] if not (e["type"] == "shield")
        ]
        cs["player_effects"] = [e for e in cs["player_effects"] if e is not None]
        if remaining > 0:
            cs["player_effects"].append({"type": "shield", "value": remaining, "turns_remaining": 99})

    # ── Apply results ──────────────────────────────────────────────────────────
    combat_event = "ongoing"
    extra_data   = {}
    victory_loot = []
    victory_xp   = 0

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
                victory_loot = list(cs.get("enemy_loot", []))
                victory_xp   = cs.get("enemy_xp", 0)
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
                    victory_loot = list(cs.get("enemy_loot", []))
                    victory_xp   = cs.get("enemy_xp", 0)
                    player = _end_combat(player, "victory", all_locations, location_key)
                else:
                    cs["round"] += 1

        if player["hp"] <= player["max_hp"] * 0.25 and player["hp"] > 0:
            player["milestones"]["times_nearly_died"] += 1

    # ── Tick down all effect durations at end of round ────────────────────────
    if combat_event == "ongoing":
        cs["player_effects"] = _tick_effects(cs["player_effects"])
        cs["enemy_effects"]  = _tick_effects(cs["enemy_effects"])

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

    # ── NPC portrait: generate once, cache in location DB ──────────────────────
    enemy_id   = cs.get("enemy_id", "")
    loc_npcs   = current_location.get("npcs", {})
    enemy_data = loc_npcs.get(enemy_id, {})
    npc_portrait = enemy_data.get("portrait", "")
    if not npc_portrait and client and enemy_data.get("description"):
        npc_portrait = generate_npc_portrait(client, cs.get("enemy_name", enemy_id), enemy_data["description"])
        if npc_portrait:
            current_location["npcs"][enemy_id]["portrait"] = npc_portrait
            save_location(location_key, current_location)

    visual_tag        = parse_tag("VISUAL", raw_text)
    enemy_description = "" if combat_event == "victory" else enemy_data.get("description", "")
    avatar_prompt     = player.get("avatar_visual_prompt", player.get("avatar_description", ""))
    scene_img = generate_scene_image(
        client, visual_tag,
        avatar_prompt,
        npc_description=enemy_description,
    )

    return {
        "text":         display_text,
        "image_base64": scene_img,
        "npc_portrait": npc_portrait,
        "status":       player["status"],
        "location":     current_location_name,
        "state":        player_to_state(player, player_id),
        "combat_event": combat_event,
        "player_dmg":   player_dmg if flee_outcome not in ("success", "captured") else 0,
        "enemy_dmg":    enemy_dmg  if flee_outcome not in ("success",)            else 0,
        "victory_loot": victory_loot,
        "victory_xp":   victory_xp,
        **extra_data,
    }
