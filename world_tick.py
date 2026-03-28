import time

from db import save_location


def tick_world(all_locations: dict) -> dict:
    """
    Called on every /action. Advances time-based state stages for any location
    entries that have elapsed their stage_duration. Saves changed locations back
    to Supabase.

    State entries in the new format look like:
    {
        "value": "cracked",
        "description": "Kael punched the east wall during a fight",
        "set_at": 1234567890.0,
        "stages": ["intact", "cracked", "collapsed", "rubble"],
        "stage_index": 1,
        "stage_duration": 7200   # seconds per stage, 0 = permanent
    }

    Old-format entries (primitives like True/False/"locked") are left untouched.
    """
    now = time.time()
    changed_keys = set()

    for loc_key, loc_data in all_locations.items():
        state = loc_data.get("state", {})
        location_dirty = False

        for flag_key, entry in list(state.items()):
            if not isinstance(entry, dict):
                continue
            stages = entry.get("stages")
            if not stages or len(stages) < 2:
                continue
            stage_duration = entry.get("stage_duration", 0)
            if stage_duration <= 0:
                continue  # permanent

            stage_index = entry.get("stage_index", 0)
            if stage_index >= len(stages) - 1:
                continue  # already at final stage

            set_at = entry.get("set_at", now)
            elapsed = now - set_at
            stages_to_advance = int(elapsed // stage_duration)

            if stages_to_advance > 0:
                new_index = min(stage_index + stages_to_advance, len(stages) - 1)
                entry["stage_index"] = new_index
                entry["value"] = stages[new_index]
                entry["set_at"] = now  # reset timer for next stage
                state[flag_key] = entry
                location_dirty = True

        if location_dirty:
            all_locations[loc_key]["state"] = state
            changed_keys.add(loc_key)

    for key in changed_keys:
        save_location(key, all_locations[key])

    return all_locations
