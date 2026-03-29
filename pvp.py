"""
pvp.py — Player vs Player turn-based combat system.
"""
import random
import time
import uuid

from combat import (
    _calc_player_damage_range, _sum_effect, _has_effect,
    _add_effect, _tick_effects,
)


# ── Fight state helpers ────────────────────────────────────────────────────────

def create_fight(challenger_id: str, target_id: str, location: str) -> dict:
    return {
        "fight_id":      str(uuid.uuid4())[:8],
        "challenger_id": challenger_id,
        "target_id":     target_id,
        "location":      location,
        "status":        "pending",   # pending → active → finished
        "whose_turn":    challenger_id,
        "round":         1,
        "players": {
            challenger_id: {"effects": [], "skill_cooldowns": {}},
            target_id:     {"effects": [], "skill_cooldowns": {}},
        },
        "log":       [],
        "winner":    None,
        "created_at": time.time(),
    }


def get_pvp_fights(world_state: dict) -> dict:
    return world_state.setdefault("pvp_fights", {})


def get_pvp_challenges(world_state: dict) -> dict:
    return world_state.setdefault("pvp_challenges", {})


def find_active_fight(world_state: dict, player_id: str) -> dict | None:
    for fight in get_pvp_fights(world_state).values():
        if fight["status"] == "active" and player_id in (fight["challenger_id"], fight["target_id"]):
            return fight
    return None


def find_pending_challenge(world_state: dict, target_id: str) -> dict | None:
    challenges = get_pvp_challenges(world_state)
    return challenges.get(target_id)


def expire_old_challenges(world_state: dict, ttl: int = 60):
    """Remove challenges older than ttl seconds."""
    now = time.time()
    challenges = get_pvp_challenges(world_state)
    expired = [k for k, v in challenges.items() if now - v.get("created_at", 0) > ttl]
    for k in expired:
        del challenges[k]


def expire_old_fights(world_state: dict, ttl: int = 300):
    """Remove finished fights older than ttl seconds."""
    now = time.time()
    fights = get_pvp_fights(world_state)
    finished = [
        k for k, v in fights.items()
        if v["status"] == "finished" and now - v.get("created_at", 0) > ttl
    ]
    for k in finished:
        del fights[k]


# ── Turn processing ────────────────────────────────────────────────────────────

def _opponent_id(fight: dict, player_id: str) -> str:
    if fight["challenger_id"] == player_id:
        return fight["target_id"]
    return fight["challenger_id"]


def _get_skill_def(player: dict, skill_id: str, skill_defs: dict) -> dict:
    """Merge world skill_defs with player custom skills."""
    merged = {**skill_defs, **player.get("skills", {})}
    return merged.get(skill_id, {})


def process_pvp_turn(
    fight: dict,
    acting_player: dict,
    action: str,
    opponent: dict,
    acting_id: str,
    opponent_id: str,
    skill_defs: dict,
) -> dict:
    """
    Process one turn of PvP combat.
    Returns updated (fight, acting_player, opponent, result_dict).
    """
    action_lower = action.lower()
    pstate = fight["players"][acting_id]
    ostate = fight["players"][opponent_id]

    # ── Flee ──────────────────────────────────────────────────────────────────
    flee_keywords = ["flee", "run", "escape", "retreat", "surrender", "forfeit"]
    if any(kw in action_lower for kw in flee_keywords):
        fight["status"] = "finished"
        fight["winner"] = opponent_id
        fight["log"].append(f"{acting_player['name']} fled the duel.")
        return {"pvp_event": "fled", "loser": acting_id, "winner": opponent_id, "log": fight["log"][-5:]}

    # ── Detect skill ──────────────────────────────────────────────────────────
    used_skill_id = None
    for skill_id in acting_player.get("skills", {}):
        skill_def = _get_skill_def(acting_player, skill_id, skill_defs)
        skill_name = skill_def.get("name", skill_id).lower()
        if skill_name in action_lower or skill_id.replace("_", " ") in action_lower:
            used_skill_id = skill_id
            break

    skill_def = _get_skill_def(acting_player, used_skill_id, skill_defs) if used_skill_id else {}

    # ── Cooldown check ────────────────────────────────────────────────────────
    cooldowns = pstate.get("skill_cooldowns", {})
    if used_skill_id and cooldowns.get(used_skill_id, 0) > 0:
        used_skill_id = None
        skill_def = {}

    # ── Mana / stamina check ──────────────────────────────────────────────────
    if used_skill_id:
        mana_cost    = skill_def.get("mana_cost", 0)
        stamina_cost = skill_def.get("stamina_cost", 0)
        if acting_player.get("mana", 0) < mana_cost or acting_player.get("stamina", 0) < stamina_cost:
            used_skill_id = None
            skill_def = {}
        else:
            acting_player["mana"]    = max(0, acting_player.get("mana", 0)    - mana_cost)
            acting_player["stamina"] = max(0, acting_player.get("stamina", 0) - stamina_cost)

    # ── Stun check ────────────────────────────────────────────────────────────
    acting_stunned = _has_effect(pstate["effects"], "stun")

    # ── Speed roll (AGI-based, determines who hits first) ─────────────────────
    acting_agi = acting_player["attributes"].get("AGI", 0)
    opp_agi    = opponent["attributes"].get("AGI", 0)
    acting_roll = acting_agi + random.randint(1, 6)
    opp_roll    = opp_agi    + random.randint(1, 6)
    acting_first = acting_roll >= opp_roll

    # ── Damage calculations ────────────────────────────────────────────────────
    merged_defs = {**skill_defs, **acting_player.get("skills", {})}
    p_min, p_max = _calc_player_damage_range(acting_player, used_skill_id, merged_defs)

    # Opponent hits back with a basic attack (no skill on their passive counter)
    o_min = max(1, opponent["derived_stats"]["atk"] - acting_player["derived_stats"]["def"] - 1)
    o_max = max(1, opponent["derived_stats"]["atk"] - acting_player["derived_stats"]["def"] + 2)

    # Apply crit / weaken modifiers to acting player
    if _has_effect(pstate["effects"], "crit"):
        p_max = int(p_max * 1.5)
    if _has_effect(pstate["effects"], "weaken"):
        p_min = max(1, p_min // 2)
        p_max = max(1, p_max // 2)

    # Apply block / dodge to opponent's incoming damage
    if _has_effect(ostate["effects"], "block"):
        block_pct = _sum_effect(ostate["effects"], "block") / 100
        p_min = max(0, int(p_min * (1 - block_pct)))
        p_max = max(0, int(p_max * (1 - block_pct)))

    acting_dmg = 0 if acting_stunned else random.randint(p_min, p_max)
    opp_dmg    = random.randint(o_min, o_max) if not _has_effect(ostate["effects"], "stun") else 0

    # Shield absorption
    opp_shield = _sum_effect(ostate["effects"], "shield")
    if opp_shield > 0:
        absorbed   = min(opp_shield, acting_dmg)
        acting_dmg = max(0, acting_dmg - absorbed)
        remaining  = opp_shield - absorbed
        ostate["effects"] = [
            ({**e, "value": remaining} if e["type"] == "shield" and remaining > 0 else None)
            for e in ostate["effects"] if e["type"] != "shield"
        ]
        ostate["effects"] = [e for e in ostate["effects"] if e is not None]

    p_shield = _sum_effect(pstate["effects"], "shield")
    if p_shield > 0:
        absorbed  = min(p_shield, opp_dmg)
        opp_dmg   = max(0, opp_dmg - absorbed)
        remaining = p_shield - absorbed
        pstate["effects"] = [
            ({**e, "value": remaining} if e["type"] == "shield" and remaining > 0 else None)
            for e in pstate["effects"] if e["type"] != "shield"
        ]
        pstate["effects"] = [e for e in pstate["effects"] if e is not None]

    # ── Apply damage in speed order ───────────────────────────────────────────
    if acting_first:
        opponent["hp"] = max(0, opponent["hp"] - acting_dmg)
        if opponent["hp"] > 0:
            acting_player["hp"] = max(0, acting_player["hp"] - opp_dmg)
    else:
        acting_player["hp"] = max(0, acting_player["hp"] - opp_dmg)
        if acting_player["hp"] > 0:
            opponent["hp"] = max(0, opponent["hp"] - acting_dmg)

    # ── Apply skill effects ───────────────────────────────────────────────────
    if used_skill_id and skill_def:
        eff_type = skill_def.get("effect", "")
        eff_val  = skill_def.get("effect_value", 0)
        eff_dur  = skill_def.get("effect_duration", 0)
        if eff_type and eff_dur > 0:
            # Offensive effects go on opponent, defensive on self
            offensive = {"poison", "bleed", "stun", "weaken", "expose"}
            if eff_type in offensive:
                ostate["effects"] = _add_effect(ostate["effects"], eff_type, eff_val, eff_dur)
            else:
                pstate["effects"] = _add_effect(pstate["effects"], eff_type, eff_val, eff_dur)

        # Set cooldown
        cd = skill_def.get("cooldown_turns", 0)
        if cd > 0:
            cooldowns[used_skill_id] = cd
        pstate["skill_cooldowns"] = cooldowns

    # ── DoT ticks on opponent ─────────────────────────────────────────────────
    poison_dmg = _sum_effect(ostate["effects"], "poison")
    bleed_dmg  = _sum_effect(ostate["effects"], "bleed")
    dot_dmg    = poison_dmg + bleed_dmg
    if dot_dmg > 0:
        opponent["hp"] = max(0, opponent["hp"] - dot_dmg)

    # ── Tick effect durations ─────────────────────────────────────────────────
    pstate["effects"] = _tick_effects(pstate["effects"])
    ostate["effects"] = _tick_effects(ostate["effects"])
    for k in list(cooldowns.keys()):
        cooldowns[k] -= 1
        if cooldowns[k] <= 0:
            del cooldowns[k]

    # ── Log entry ─────────────────────────────────────────────────────────────
    log_entry = f"Round {fight['round']}: {acting_player['name']} dealt {acting_dmg} dmg"
    if not acting_stunned:
        if used_skill_id:
            log_entry += f" ({skill_def.get('name', used_skill_id)})"
    else:
        log_entry += " [stunned]"
    log_entry += f", {opponent['name']} dealt {opp_dmg} dmg back."
    if dot_dmg:
        log_entry += f" DoT: {dot_dmg}."
    fight["log"].append(log_entry)
    fight["log"] = fight["log"][-10:]

    # ── Check win condition ───────────────────────────────────────────────────
    pvp_event = "ongoing"
    winner_id = None

    if acting_player["hp"] <= 0 and opponent["hp"] <= 0:
        # Both dead — challenger wins tiebreak
        winner_id = fight["challenger_id"]
        fight["status"] = "finished"
        fight["winner"] = winner_id
        pvp_event = "finished"
    elif opponent["hp"] <= 0:
        winner_id = acting_id
        fight["status"] = "finished"
        fight["winner"] = winner_id
        pvp_event = "finished"
    elif acting_player["hp"] <= 0:
        winner_id = opponent_id
        fight["status"] = "finished"
        fight["winner"] = winner_id
        pvp_event = "finished"
    else:
        # Flip turn
        fight["whose_turn"] = opponent_id
        fight["round"] += 1

    return {
        "pvp_event":   pvp_event,
        "winner":      winner_id,
        "acting_dmg":  acting_dmg,
        "opp_dmg":     opp_dmg,
        "dot_dmg":     dot_dmg,
        "skill_used":  skill_def.get("name", used_skill_id) if used_skill_id else None,
        "log":         fight["log"][-5:],
        "acting_first": acting_first,
    }
