"""
migrate_map.py — adds 10 new locations, updates existing exits, adds x/y coordinates to all locations.
Run once: python migrate_map.py
Safe to re-run (upserts only).
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


# ── Coordinates for all locations (existing + new) ─────────────────────────────
# Grid units. x increases right, y increases down.
COORDINATES = {
    # Void Wastes (top)
    "shattered_spire":       {"x": 7, "y": 0},
    "void_chasm_edge":       {"x": 6, "y": 1},
    "watchtower_peak":       {"x": 1, "y": 1},
    "void_wastes_edge":      {"x": 6, "y": 2},
    # Bridge zone (middle)
    "crumbling_watchtower":  {"x": 1, "y": 2},
    "void_bridge":           {"x": 5, "y": 3},
    "forgotten_camp":        {"x": 7, "y": 3},
    "old_barracks":          {"x": 9, "y": 3},
    # Ashen ruins (left)
    "ashen_courtyard":       {"x": 2, "y": 4},
    "ruined_keep":           {"x": 4, "y": 4},
    # Saltmarsh (right)
    "saltmarsh_gate":        {"x": 8, "y": 4},
    "the_ashen_flagon":      {"x": 10, "y": 4},
    "tavern_back_room":      {"x": 12, "y": 4},
    # Lower ashen ruins
    "ash_burial_grounds":    {"x": 0, "y": 5},
    "sunken_library":        {"x": 2, "y": 5},
    "void_altar":            {"x": 4, "y": 5},
    # Lower saltmarsh
    "saltmarsh_market":      {"x": 9, "y": 5},
    "underground_vault":     {"x": 12, "y": 5},
    # Deepest level
    "throne_vault":          {"x": 4, "y": 6},
    "dockside":              {"x": 8, "y": 6},
    "healers_hut":           {"x": 10, "y": 6},
}

# ── New locations ──────────────────────────────────────────────────────────────
NEW_LOCATIONS = {
    "crumbling_watchtower": {
        "name": "Crumbling Watchtower",
        "type": "location",
        "parent": "ashen_ruins",
        "description": "A hollow stone tower leaning at a precarious angle above the courtyard. The interior stairs are missing half their steps, but the structure still stands — barely. Ash has settled in thick drifts along the base. A narrow window slit offers a partial view of the bridge.",
        "exits": ["ashen_courtyard", "watchtower_peak"],
        "npcs": {},
        "items": ["loose_stone", "old_rope"],
        "state": {
            "upper_stairs_intact": False,
            "arrow_slit_blocked": False,
        },
        "history": [],
    },
    "watchtower_peak": {
        "name": "Watchtower Peak",
        "type": "room",
        "parent": "ashen_ruins",
        "description": "The open crown of the tower. The view from here stretches across the entire Ashen Ruins — the glowing Void Bridge, the distant outline of Saltmarsh clinging to the island's edge, and the darkness of the Void Below yawning in every direction. Wind howls constantly. Someone left a spyglass here.",
        "exits": ["crumbling_watchtower"],
        "npcs": {},
        "items": ["cracked_spyglass"],
        "state": {
            "spyglass_taken": False,
            "signal_fire_lit": False,
        },
        "history": [],
    },
    "ash_burial_grounds": {
        "name": "Ash Burial Grounds",
        "type": "location",
        "parent": "ashen_ruins",
        "description": "Rows of cracked grave markers disappearing into ash drifts. Most are nameless, inscriptions worn to nothing by three centuries of ash-fall. The void energy here spikes unpredictably. Something shifts beneath certain mounds when it does.",
        "exits": ["ashen_courtyard"],
        "npcs": {
            "burial_shade": {
                "name": "Burial Shade",
                "status": "undead",
                "disposition": -30,
                "hp": 999, "max_hp": 999, "atk": 0, "def": 999,
                "xp_reward": 0,
                "loot": [],
                "memory": [],
                "description": "A translucent figure in burial wrappings that drifts between the grave markers. It cannot be harmed. It whispers names — some of them recent.",
            }
        },
        "items": ["grave_marker_fragment", "ash_offering"],
        "state": {
            "graves_disturbed": False,
            "shade_appeased": False,
        },
        "history": [],
    },
    "void_altar": {
        "name": "The Void Altar",
        "type": "room",
        "parent": "ashen_ruins",
        "description": "A circular chamber beneath the keep, separate from the throne vault. A cracked obsidian altar still hums with residual power. Burn marks radiate outward from the center in a perfect star pattern — the scar of the ritual that shattered the Crown three hundred years ago. The air tastes of metal.",
        "exits": ["ruined_keep"],
        "npcs": {},
        "items": ["void_crown_fragment", "ritual_ash"],
        "state": {
            "altar_active": False,
            "ritual_circle_intact": True,
            "crown_fragment_taken": False,
        },
        "history": [],
    },
    "forgotten_camp": {
        "name": "The Forgotten Camp",
        "type": "location",
        "parent": "ashen_ruins",
        "description": "A temporary camp that became permanent. Six weather-beaten tents surround a cold fire pit. Most of the original occupants are bones now, half-buried in ash. Someone recent has been here — the ash around the fire pit is disturbed and a bedroll is relatively clean. A useful waypoint between the ruins and Saltmarsh.",
        "exits": ["void_bridge", "saltmarsh_gate"],
        "npcs": {},
        "items": ["bedroll", "empty_ration_tin", "torn_map_piece"],
        "state": {
            "fire_lit": False,
            "camp_searched": False,
            "recent_visitor": True,
        },
        "history": [],
    },
    "old_barracks": {
        "name": "Old Saltmarsh Barracks",
        "type": "location",
        "parent": "saltmarsh_settlement",
        "description": "A long building repurposed as communal housing for Saltmarsh's overflow population. Dozens of refugees sleep in shifts on salvaged cots. The smell of old sweat and ash is overwhelming. A corkboard near the entrance is plastered with missing-person notices, crude maps, and pleas for information about people lost in the ruins.",
        "exits": ["saltmarsh_gate", "saltmarsh_market"],
        "npcs": {
            "refugee_elder": {
                "name": "Elder Voss",
                "status": "alive",
                "disposition": 10,
                "hp": 15, "max_hp": 15, "atk": 1, "def": 0,
                "xp_reward": 0,
                "loot": [],
                "memory": [],
                "description": "An elderly man who arrived in Saltmarsh five years ago and never left. He knows the names and faces of every refugee who has passed through. He keeps meticulous records in a battered ledger.",
            }
        },
        "items": ["missing_persons_notice", "refugees_ledger"],
        "state": {
            "corkboard_read": False,
            "ledger_found": False,
        },
        "history": [],
    },
    "underground_vault": {
        "name": "The Underground Vault",
        "type": "room",
        "parent": "saltmarsh_settlement",
        "description": "The chamber below the Ashen Flagon, accessed through the padlocked trapdoor. Stone walls, no windows, a single oil lamp. Shelves hold void artifacts, unlabeled vials, and bundled old-kingdom documents tied with black ribbon. Someone has been keeping this very organized — and very secret.",
        "exits": ["tavern_back_room"],
        "npcs": {},
        "items": ["void_artifact_bundle", "unlabeled_vial", "kingdom_documents"],
        "state": {
            "vault_searched": False,
            "candle_lit": False,
            "documents_read": False,
        },
        "history": [],
    },
    "dockside": {
        "name": "Saltmarsh Dockside",
        "type": "location",
        "parent": "saltmarsh_settlement",
        "description": "The ragged edge of the floating island. Rope bridges and salvaged planking extend precariously over the Void Below, where salvagers haul up wreckage on long winch-lines. The wind here is constant and sharp. Far below, if you look long enough, shapes move in the dark — things that are not wreckage.",
        "exits": ["saltmarsh_market"],
        "npcs": {
            "salvager_dom": {
                "name": "Dom",
                "status": "alive",
                "disposition": 5,
                "hp": 30, "max_hp": 30, "atk": 6, "def": 2,
                "xp_reward": 0,
                "loot": ["salvage_token"],
                "memory": [],
                "description": "A wiry salvager with burn-scarred hands from void-touched wreckage. Works the winch-line alone since his partner fell in. Doesn't talk about it.",
            }
        },
        "items": ["salvaged_pulley", "void_touched_debris"],
        "state": {
            "winch_operational": True,
            "something_seen_below": False,
        },
        "history": [],
    },
    "void_chasm_edge": {
        "name": "Void Chasm Edge",
        "type": "location",
        "parent": "void_wastes",
        "description": "The absolute edge of the island remnant, where the rock drops away into infinite darkness. Nothing below but black and the distant sound of something vast breathing. Standing here causes nosebleeds, temporal disorientation, and the persistent feeling of being watched from below.",
        "exits": ["void_wastes_edge", "shattered_spire"],
        "npcs": {},
        "items": ["void_worn_stone"],
        "state": {
            "player_warned": False,
            "something_noticed_below": False,
        },
        "history": [],
    },
    "shattered_spire": {
        "name": "The Shattered Spire",
        "type": "location",
        "parent": "void_wastes",
        "description": "A needle of rock barely wide enough to stand on, connected to the main island by a natural stone arch. Void energy is so thick here it is visible — purple fog drifts at knee height, and the air crackles with static that makes hair stand on end. A massive, robed figure stands motionless at the far end, facing the void.",
        "exits": ["void_chasm_edge"],
        "npcs": {
            "void_sentinel": {
                "name": "The Void Sentinel",
                "status": "alive",
                "disposition": -100,
                "hp": 80, "max_hp": 80, "atk": 14, "def": 6,
                "xp_reward": 150,
                "loot": ["void_crown_shard_2", "sentinel_robes"],
                "memory": [],
                "description": "A towering figure in disintegrating robes, its face hidden beneath a hood that emits faint purple light. It has stood here for three hundred years, bound by the same ritual that shattered the Crown. It does not speak. It only attacks.",
            }
        },
        "items": [],
        "state": {
            "sentinel_defeated": False,
            "shard_taken": False,
        },
        "history": [],
    },
}

# ── Exit additions to existing locations ───────────────────────────────────────
EXIT_ADDITIONS = {
    "ashen_courtyard": ["crumbling_watchtower", "ash_burial_grounds"],
    "ruined_keep":     ["void_altar"],
    "saltmarsh_gate":  ["old_barracks", "forgotten_camp"],
    "saltmarsh_market":["dockside"],
    "tavern_back_room":["underground_vault"],
    "void_wastes_edge":["void_chasm_edge"],
    "void_bridge":     ["forgotten_camp"],
}


def run():
    print("Loading existing locations...")
    res = sb.table("locations").select("key, data").execute()
    existing = {row["key"]: row["data"] for row in res.data}

    # ── 1. Add coordinates to all existing locations ───────────────────────────
    print("\n[1/3] Adding coordinates to existing locations...")
    for key, coords in COORDINATES.items():
        if key in existing:
            loc = existing[key]
            loc["x"] = coords["x"]
            loc["y"] = coords["y"]
            sb.table("locations").update({"data": loc}).eq("key", key).execute()
            print(f"  ✓ {key} → ({coords['x']}, {coords['y']})")

    # ── 2. Update exits on existing locations ──────────────────────────────────
    print("\n[2/3] Updating exits on existing locations...")
    for key, new_exits in EXIT_ADDITIONS.items():
        if key not in existing:
            print(f"  ! {key} not found, skipping")
            continue
        loc = existing[key]
        current_exits = loc.get("exits", [])
        added = []
        for e in new_exits:
            if e not in current_exits:
                current_exits.append(e)
                added.append(e)
        loc["exits"] = current_exits
        if "x" not in loc and key in COORDINATES:
            loc["x"] = COORDINATES[key]["x"]
            loc["y"] = COORDINATES[key]["y"]
        sb.table("locations").update({"data": loc}).eq("key", key).execute()
        if added:
            print(f"  ✓ {key} ← added exits: {added}")
        else:
            print(f"  ~ {key} exits unchanged")

    # ── 3. Insert new locations ────────────────────────────────────────────────
    print("\n[3/3] Inserting new locations...")
    for key, data in NEW_LOCATIONS.items():
        coords = COORDINATES.get(key, {"x": 0, "y": 0})
        data["x"] = coords["x"]
        data["y"] = coords["y"]
        sb.table("locations").upsert({"key": key, "data": data}).execute()
        print(f"  ✓ {key} — {data['name']}")

    print("\nDone. Run the server and check /map.json to verify.")


if __name__ == "__main__":
    run()
