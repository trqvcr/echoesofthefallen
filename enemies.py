import random
import time

from db import save_location

# ── Enemy Definitions ──────────────────────────────────────────────────────────
# Enemies are not hardcoded in location data. The spawn system injects them
# dynamically at runtime based on respawn timers.

# ── Story NPC Respawn Pool ─────────────────────────────────────────────────────
# These NPCs live in fixed locations. When killed they respawn after the given
# time (they return to town, recover, or another person takes up the role).

STORY_NPC_POOL = {
    "vendor_petra": {
        "location": "saltmarsh_market",
        "respawn_seconds": 600,   # 10 min
        "npc": {
            "name": "Petra", "status": "alive", "disposition": 50,
            "hp": 15, "max_hp": 15, "atk": 3, "def": 1,
            "xp_reward": 0, "loot": [],  "memory": [],
            "description": "A wiry merchant woman with ink-stained fingers and sharp eyes. She trades in salvaged weapons, armor, and relics from the ruins. She never asks where things come from.",
        },
    },
    "gate_guard_maren": {
        "location": "saltmarsh_gate",
        "respawn_seconds": 480,   # 8 min
        "npc": {
            "name": "Maren", "status": "alive", "disposition": 0,
            "hp": 20, "max_hp": 20, "atk": 5, "def": 2,
            "xp_reward": 0, "loot": [], "memory": [],
            "description": "A broad-shouldered gate guard in dented plate. Watchful, tired, and underpaid. She lets travelers through without much fuss but keeps a hand near her sword.",
        },
    },
    "osric": {
        "location": "the_ashen_flagon",
        "respawn_seconds": 360,   # 6 min
        "npc": {
            "name": "Osric", "status": "alive", "disposition": 30,
            "hp": 18, "max_hp": 18, "atk": 4, "def": 1,
            "xp_reward": 0, "loot": [], "memory": [],
            "description": "A one-armed barkeep, missing his left arm from the elbow down. He lost it during the Shattering. He runs the Ashen Flagon with quiet authority. He knows more about the ruins than he lets on.",
        },
    },
    "sable": {
        "location": "healers_hut",
        "respawn_seconds": 300,   # 5 min
        "npc": {
            "name": "Sable", "status": "alive", "disposition": 60,
            "hp": 12, "max_hp": 12, "atk": 2, "def": 0,
            "xp_reward": 0, "loot": [], "memory": [],
            "description": "A quiet healer who rarely speaks above a whisper. Her hands are always warm. She asks no questions and charges only what people can spare.",
        },
    },
    "salvager_dom": {
        "location": "dockside",
        "respawn_seconds": 420,   # 7 min
        "npc": {
            "name": "Dom", "status": "alive", "disposition": 5,
            "hp": 16, "max_hp": 16, "atk": 4, "def": 1,
            "xp_reward": 0, "loot": [], "memory": [],
            "description": "A sun-beaten salvager with rope-burned hands. He hauls things out of the void-water for coin. Gruff but fair.",
        },
    },
}


def tick_story_npcs(all_locations: dict) -> dict:
    """Respawn story NPCs that have been dead long enough."""
    now          = time.time()
    changed_keys = set()

    for npc_id, definition in STORY_NPC_POOL.items():
        loc_key = definition["location"]
        loc     = all_locations.get(loc_key)
        if not loc:
            continue

        npc = loc.get("npcs", {}).get(npc_id)
        if not npc or npc.get("status") != "dead":
            continue

        died_at = npc.get("died_at", 0)
        if died_at and (now - died_at) >= definition["respawn_seconds"]:
            restored = dict(definition["npc"])   # fresh copy
            restored["memory"] = list(npc.get("memory", []))  # keep their memories
            loc.setdefault("npcs", {})[npc_id] = restored
            all_locations[loc_key] = loc
            changed_keys.add(loc_key)

    for key in changed_keys:
        save_location(key, all_locations[key])

    return all_locations


# ── Enemy Definitions ──────────────────────────────────────────────────────────

ENEMY_POOL = {
    "void_wolf": {
        "name": "Void-Touched Wolf",
        "status": "alive",
        "disposition": -100,
        "hp": 20, "max_hp": 20, "atk": 5, "def": 1,
        "xp_reward": 30,
        "loot": ["void_fang", "shredded_leather"],
        "memory": [],
        "description": "A large wolf whose fur has turned ashen grey. Void energy pulses beneath its skin in veins of purple light.",
        "valid_locations": ["ruined_keep", "ashen_courtyard", "void_bridge"],
        "max_alive": 2,
        "respawn_seconds": 120,
    },
    "void_shade": {
        "name": "Void Shade",
        "status": "alive",
        "disposition": -100,
        "hp": 15, "max_hp": 15, "atk": 7, "def": 0,
        "xp_reward": 25,
        "loot": ["shadow_essence"],
        "memory": [],
        "description": "A flickering humanoid shape of pure void energy. It moves faster than the eye can follow.",
        "valid_locations": ["void_bridge", "void_wastes_edge", "sunken_library"],
        "max_alive": 2,
        "respawn_seconds": 180,
    },
}


# ── Spawn System ───────────────────────────────────────────────────────────────

def tick_spawns(all_locations: dict) -> dict:
    """
    Called on every /action. Checks if any roaming enemies should respawn
    and injects them into a random valid location.
    Saves changed locations back to Supabase.
    """
    now = time.time()
    changed_keys = set()

    for enemy_id, enemy_def in ENEMY_POOL.items():
        alive_count = sum(
            1 for loc in all_locations.values()
            if loc.get("npcs", {}).get(enemy_id, {}).get("status") == "alive"
        )

        if alive_count >= enemy_def["max_alive"]:
            continue

        # Find the most recent death time for this enemy across all locations
        died_at = max(
            (loc.get("npcs", {}).get(enemy_id, {}).get("died_at", 0)
             for loc in all_locations.values()),
            default=0
        )

        if died_at == 0 or (now - died_at) >= enemy_def["respawn_seconds"]:
            candidates = [
                loc_key for loc_key in enemy_def["valid_locations"]
                if loc_key in all_locations and
                all_locations[loc_key].get("npcs", {}).get(enemy_id, {}).get("status") != "alive"
            ]
            if not candidates:
                continue

            spawn_key = random.choice(candidates)
            loc = all_locations[spawn_key]
            if "npcs" not in loc:
                loc["npcs"] = {}

            loc["npcs"][enemy_id] = {
                "name":        enemy_def["name"],
                "status":      "alive",
                "disposition": enemy_def["disposition"],
                "hp":          enemy_def["hp"],
                "max_hp":      enemy_def["max_hp"],
                "atk":         enemy_def["atk"],
                "def":         enemy_def["def"],
                "xp_reward":   enemy_def["xp_reward"],
                "loot":        list(enemy_def["loot"]),
                "memory":      [],
                "description": enemy_def["description"],
            }
            all_locations[spawn_key] = loc
            changed_keys.add(spawn_key)

    for key in changed_keys:
        save_location(key, all_locations[key])

    return all_locations
