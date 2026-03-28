import random
import time

from db import save_location

# ── Enemy Definitions ──────────────────────────────────────────────────────────
# Enemies are not hardcoded in location data. The spawn system injects them
# dynamically at runtime based on respawn timers.

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
