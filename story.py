"""
story.py — Main storyline definitions, nudge logic, and world event helpers.
"""
import time

# ── Act Definitions ────────────────────────────────────────────────────────────

ACTS = {
    1: {
        "name": "The Awakening",
        "context": (
            "The void is slowly consuming the island. Tremors crack the ruins. "
            "Survivors whisper of a cult deep in the Void Wastes performing a ritual "
            "to deliberately tear open the void rift. The threat feels distant — but growing. "
            "Explorers who venture north report strange chanting and an unnatural red glow."
        ),
        "tone": "dread and mystery — danger is real but not yet urgent",
        "next_beat": "Reach the Void Wastes and learn what the cult is doing.",
    },
    2: {
        "name": "The Ritual",
        "context": (
            "The cult's ritual is nearly complete. The void rift above the Void Wastes "
            "is visibly widening — a tear of black and crimson across the sky. "
            "Creatures pour through in greater numbers each night. "
            "The Void Cultist Leader must be killed and the Ritual Shard destroyed "
            "before the dark moon rises, or the island is lost."
        ),
        "tone": "urgency and desperation — every action matters",
        "next_beat": "Kill the Void Cultist Leader and destroy the Ritual Shard.",
    },
    3: {
        "name": "The Reckoning",
        "context": (
            "The ritual is complete. The Void Entity has awakened inside the Ritual Chamber "
            "at the heart of the Void Wastes. The island is dying — stone crumbling into void, "
            "ash raining upward. The Entity must be destroyed. "
            "There may not be another heir to carry this on."
        ),
        "tone": "apocalyptic and final — everything is on the line",
        "next_beat": "Enter the Ritual Chamber and destroy the Void Entity.",
    },
}

# ── Story Flags ────────────────────────────────────────────────────────────────
# These can be set by Gemini (via mutation) or hardcoded (boss death, location visit).

STORY_FLAGS = {
    "void_wastes_reached":   "Player first entered the Void Wastes",
    "scholar_warned":        "Player spoke with the Ashen Scholar about the ritual",
    "ritual_shard_found":    "Player found a void shard fragment",
    "cult_leader_dead":      "The Void Cultist Leader has been slain",
    "ritual_chamber_opened": "The sealed Ritual Chamber has been unlocked",
    "void_entity_defeated":  "The Void Entity has been destroyed — the island is saved",
}

# ── Act Advancement Conditions ─────────────────────────────────────────────────

def check_act_advancement(story: dict) -> int:
    """Returns the act the world should be in based on current flags/stats."""
    act   = story.get("act", 1)
    flags = story.get("flags", {})
    stats = story.get("stats", {})

    if act == 1:
        if flags.get("void_wastes_reached") and stats.get("total_kills", 0) >= 10:
            return 2
    if act == 2:
        if flags.get("cult_leader_dead") and flags.get("ritual_shard_found"):
            return 3
    return act


# ── World Events ───────────────────────────────────────────────────────────────
# Stored in world["story"]["world_event"]. Expires after TTL seconds.

EVENT_TTL = 300  # 5 minutes

WORLD_EVENTS = {
    "act_2_begins": {
        "title":   "THE RITUAL ACCELERATES",
        "message": (
            "A tremor shakes the entire island. In the Void Wastes, the rift tears wider — "
            "a gash of crimson light visible from every corner of the island. "
            "The cult is no longer hiding. The dark moon approaches."
        ),
        "color": "red",
    },
    "act_3_begins": {
        "title":   "THE VOID AWAKENS",
        "message": (
            "The island screams. Stone splits. The sky above the Void Wastes collapses inward "
            "as something vast and ancient pulls itself through the rift. "
            "The Void Entity has awakened. This is the end — or the beginning of one."
        ),
        "color": "purple",
    },
    "cult_leader_killed": {
        "title":   "THE CULT LEADER FALLS",
        "message": (
            "A shockwave of void energy bursts outward from the Wastes. "
            "Somewhere on the island, a player has slain the Void Cultist Leader. "
            "The ritual wavers — but it is not yet stopped."
        ),
        "color": "red",
    },
    "void_entity_defeated": {
        "title":   "THE VOID RETREATS",
        "message": (
            "The rift closes. The howling stops. For the first time in memory, "
            "the sky above the island is silent. "
            "A player has destroyed the Void Entity. The island endures — for now."
        ),
        "color": "purple",
    },
}


def make_world_event(event_id: str, triggered_by: str = "") -> dict:
    template = WORLD_EVENTS.get(event_id, {})
    return {
        "id":           event_id,
        "title":        template.get("title", "WORLD EVENT"),
        "message":      template.get("message", "Something has changed."),
        "color":        template.get("color", "purple"),
        "triggered_by": triggered_by,
        "expires_at":   time.time() + EVENT_TTL,
    }


def get_active_world_event(story: dict) -> dict | None:
    event = story.get("world_event")
    if event and event.get("expires_at", 0) > time.time():
        return event
    return None


# ── Nudge Logic ────────────────────────────────────────────────────────────────

NUDGE_THRESHOLD = 6  # turns without story progress before nudging

def get_story_nudge(story: dict, turns_without_progress: int) -> str:
    """
    Returns a nudge string to inject into the AI prompt if the player hasn't
    made story progress recently. Empty string if no nudge needed.
    """
    if turns_without_progress < NUDGE_THRESHOLD:
        return ""

    act        = story.get("act", 1)
    flags      = story.get("flags", {})
    act_data   = ACTS.get(act, ACTS[1])
    next_beat  = act_data["next_beat"]

    # Pick the most relevant specific hint based on unfulfilled flags
    if act == 1:
        if not flags.get("scholar_warned"):
            hint = "An NPC, environmental detail, or overheard fragment hints that a scholar in the Ashen Ruins knows something about the strange events."
        elif not flags.get("void_wastes_reached"):
            hint = "Something in the environment — a distant red glow, falling ash, a dead traveler's note — points north toward the Void Wastes."
        else:
            hint = f"Subtly reference: {next_beat}"
    elif act == 2:
        if not flags.get("ritual_shard_found"):
            hint = "A dead cultist, a discarded note, or a strange energy trail hints at the existence of a Ritual Shard somewhere in the Void Wastes."
        else:
            hint = "The cult leader is still out there. An NPC, creature behavior, or environmental sign points toward a confrontation."
    else:
        hint = "The Ritual Chamber pulses with void energy. Something draws the player toward it."

    return (
        f"STORY NUDGE (do not mention this mechanic): {hint} "
        f"Weave it organically into the narrative — one sentence is enough. Do not be heavy-handed."
    )


# ── Context String for AI Prompts ─────────────────────────────────────────────

def get_story_context(story: dict) -> str:
    act      = story.get("act", 1)
    act_data = ACTS.get(act, ACTS[1])
    flags    = story.get("flags", {})
    active   = [k for k, v in flags.items() if v]

    ctx = (
        f"STORY ACT {act} — {act_data['name']}\n"
        f"{act_data['context']}\n"
        f"NARRATIVE TONE: {act_data['tone']}\n"
    )
    if active:
        ctx += f"STORY FLAGS ACHIEVED: {', '.join(active)}\n"
    return ctx
