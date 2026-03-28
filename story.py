"""
story.py — Story definitions, NPC knowledge, corruption system, and world events.
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

STORY_FLAGS = {
    # Discovery
    "void_wastes_reached":        "Player first entered the Void Wastes",
    "throne_vault_visited":       "Player entered the Throne Vault",
    "sunken_library_visited":     "Player entered the Sunken Library",
    "ritual_chamber_found":       "Player found the sealed Ritual Chamber",
    # NPC interactions
    "scholar_warned":             "Player spoke with the Ashen Scholar about the ritual",
    "osric_questioned":           "Player asked Osric about the Shattering",
    "stranger_noticed":           "Player acknowledged the hooded stranger",
    "stranger_dead":              "The hooded stranger has been killed",
    "sable_warned":               "Sable mentioned wounded travelers from the Void Wastes",
    "petra_mentioned_artifacts":  "Petra mentioned strange void relics from the ruins",
    # Corruption milestones
    "corruption_25_reached":      "Void corruption reached 25% — The Creep begins",
    "corruption_50_reached":      "Void corruption reached 50% — The Encroachment",
    "corruption_75_reached":      "Void corruption reached 75% — The Breaking",
    # Corruption nodes
    "void_node_1_disrupted":      "Void corruption node in the Ruined Keep was disrupted",
    "void_node_2_disrupted":      "Void corruption node at the Void Bridge was disrupted",
    "void_node_3_disrupted":      "Void corruption node in the Void Wastes Edge was disrupted",
    # Lore discoveries
    "shattering_truth_learned":   "Player learned the truth of what caused the Shattering",
    "cult_origin_learned":        "Player learned how the void cult formed (from the stranger)",
    "void_crown_lore_learned":    "Player learned about the Void Crown from the Scholar",
    # Story progression
    "ritual_shard_1_found":       "First Void Crown shard recovered from the Throne Vault",
    "ritual_shard_2_found":       "Second Void Crown shard recovered from the Sunken Library",
    "ritual_shard_3_found":       "Third Void Crown shard recovered from the Void Wastes",
    "cult_leader_dead":           "The Void Cultist Leader has been slain",
    "ritual_chamber_opened":      "The sealed Ritual Chamber has been unlocked",
    "void_crown_assembled":       "All three shards of the Void Crown have been assembled",
    "void_entity_defeated":       "The Void Entity has been destroyed — the island is saved",
}

# ── NPC Knowledge System ───────────────────────────────────────────────────────
# Each NPC entry has:
#   always:      injected whenever the player is in their presence
#   if_flag:     hints injected when the named flag IS true (NPC reacts to world state)
#   if_not_flag: hints injected when the named flag is NOT yet true (NPC pulls player)
#   corruption:  list of (threshold, hint) — injected when corruption >= threshold

NPC_KNOWLEDGE = {
    "osric": {
        "always": (
            "Osric is a one-armed barkeep who lost his left arm in the Shattering. "
            "He runs the Ashen Flagon with quiet authority and watches the door constantly. "
            "He knows far more about the void and the ruins than he lets on."
        ),
        "if_flag": {
            "corruption_25_reached":        "Osric has been unusually quiet. He mops the bar more than necessary. The ash is falling heavier and he knows what it means.",
            "corruption_50_reached":        "Osric has started keeping a weapon behind the bar. He tells regulars to stay close to town.",
            "stranger_noticed":             "Osric keeps glancing toward the hooded stranger's corner. He clearly knows her — and is troubled by her presence.",
            "osric_questioned":             "Osric has opened up slightly. He carries guilt about the Shattering that he hasn't spoken aloud in years.",
            "shattering_truth_learned":     "Osric speaks more freely now, as if a weight has been partially lifted. He still doesn't say everything.",
            "siege_of_saltmarsh_repelled":  "Osric is grim but steady. He helped barricade the door during the siege. He offers drinks on the house to anyone who fought.",
            "cult_leader_dead":             "Osric exhales for the first time in weeks. He doesn't celebrate, but he pours a drink and leaves it on the bar.",
        },
        "if_not_flag": {
            "scholar_warned":      "Osric might mention — if the conversation turns to the tremors — that an old scholar in the eastern ruins has been watching the void shifts.",
            "void_wastes_reached": "Osric warns quietly but seriously that travelers heading north haven't been returning.",
            "osric_questioned":    "Osric is guarded about the Shattering. Something in his eyes says he wants to be asked directly.",
            "stranger_noticed":    "Osric keeps his gaze drifting to a cloaked figure sitting alone in the far corner.",
        },
        "corruption": [
            (50, "Osric is visibly shaken. He's been drinking his own stock, which he never does."),
            (75, "Osric has told the remaining regulars to arm themselves. He's seen something like this before — once — and it ended badly."),
        ],
    },

    "hooded_stranger": {
        "always": (
            "The hooded stranger sits in the darkest corner of the Ashen Flagon. "
            "She speaks carefully, as if weighing every word. "
            "She was once part of the void cult. She left. She carries that guilt like a wound."
        ),
        "if_flag": {
            "stranger_noticed":         "She has clocked the player. She will not look away first.",
            "corruption_25_reached":    "The stranger's hands are unsteady. She knows exactly what the rising corruption means.",
            "corruption_50_reached":    "The stranger has stopped eating. She stares at the door like she's deciding whether to run.",
            "cult_origin_learned":      "She has told someone the truth about the cult. She looks lighter — and more afraid.",
        },
        "if_not_flag": {
            "stranger_noticed":  "She watches any newcomer from beneath her hood. She is waiting to be noticed.",
            "stranger_dead":     "She has critical information about the void cult's ritual that she has not yet shared with anyone.",
            "cult_origin_learned": "She knows how the cult formed and where the ritual chamber is. She will share it — but only if someone earns her trust.",
        },
        "corruption": [
            (50, "She approaches players who enter the tavern rather than waiting in her corner. She is running out of time to speak."),
            (75, "She has left a folded note on the bar if no one has spoken to her: 'The chamber is beneath the Altar Stone. Find me if you want to know more.'"),
        ],
    },

    "scholars_ghost": {
        "always": (
            "The Scholar's Ghost is bound to the Sunken Library and cannot be killed — only spoken with. "
            "She was a researcher who stayed too long studying the void and never left. "
            "She knows the true history of the Shattering and the nature of the Void Crown."
        ),
        "if_flag": {
            "sunken_library_visited":   "The ghost has been watching the player since they first entered.",
            "void_crown_lore_learned":  "She has shared what she knows about the Void Crown. She speaks with greater urgency now — as if relieved to have told someone.",
            "corruption_50_reached":    "The ghost is frantic. She manifests more fully at higher corruption. Her words come faster, less composed.",
            "ritual_shard_2_found":     "The ghost grows quieter after the shard is removed. She says only: 'Now there are two. Do not wait for the third.'",
            "void_crown_assembled":     "The ghost is still. 'Whatever you choose to do with it,' she says, 'do it quickly.'",
        },
        "if_not_flag": {
            "scholar_warned":          "The ghost will try to get the player's attention if they enter the library. She has been waiting a very long time for someone.",
            "void_crown_lore_learned": "She knows what the Void Crown is and what assembling all three shards will do. She needs to be asked directly.",
            "ritual_shard_2_found":    "A shard of the Void Crown is somewhere in this library. She knows where but will only say if the player asks the right question.",
        },
        "corruption": [
            (25, "The ghost appears without being addressed, flickering: 'It's getting worse. Someone needs to act.'"),
            (75, "The ghost is distressed and barely coherent. She keeps repeating one phrase: 'The shard. The shard. The shard.'"),
        ],
    },

    "sable": {
        "always": (
            "Sable is a quiet healer who charges only what people can spare. "
            "Her hands are always warm. She sees a great deal — injured people talk when they're scared. "
            "She hears things that don't reach the rest of town."
        ),
        "if_flag": {
            "corruption_25_reached": "Sable has been treating more injuries. She mentions, matter-of-factly, that travelers from the north are arriving in worse shape than before.",
            "corruption_50_reached": "Sable has stopped accepting new patients she can't help — void burns she has no treatment for. She looks exhausted.",
            "sable_warned":          "Sable speaks more directly about what she's seen if the player has already earned her trust.",
            "void_entity_defeated":  "Sable allows herself one quiet exhale. Then she gets back to work.",
        },
        "if_not_flag": {
            "void_wastes_reached": "Sable mentions that the last three travelers from the northern road came in with void burns she'd never seen before — and wouldn't say where they'd been.",
            "sable_warned":        "Sable has been seeing wounds she can't explain. She would tell someone if they asked.",
        },
        "corruption": [
            (50, "Sable is rationing her healing supplies. She looks tired in a way that sleep won't fix."),
            (75, "Sable has barricaded the window of the healers' hut. She works by candlelight only. She doesn't explain why."),
        ],
    },

    "vendor_petra": {
        "always": (
            "Petra is a wiry merchant with ink-stained fingers and sharp, assessing eyes. "
            "She trades in salvaged weapons, armor, and relics from the ruins. "
            "She never asks where things come from — but she remembers everything she's seen pass through."
        ),
        "if_flag": {
            "corruption_25_reached":        "Petra has raised her prices. 'Supply routes are getting difficult,' she says without elaborating.",
            "petra_mentioned_artifacts":    "Petra speaks more freely about void relics if the subject has already come up — she's been sitting on this for a while.",
            "ritual_shard_1_found":         "Petra has heard rumours something was taken from the Throne Vault. She's curious and slightly nervous about it.",
        },
        "if_not_flag": {
            "ritual_shard_1_found":      "Petra mentions she's been getting unusual offers lately — buyers asking for 'crown fragments.' She turned them down. The buyers felt wrong.",
            "petra_mentioned_artifacts": "Petra has been declining to stock certain void-touched relics. They sell well — but trouble follows them.",
        },
        "corruption": [
            (50, "Petra has started packing her most valuable stock into a lockbox. She isn't leaving yet — but she's thinking about it."),
            (75, "Petra only sells to people she recognises. She eyes strangers with open suspicion and keeps her hand near a knife."),
        ],
    },

    "gate_guard_maren": {
        "always": (
            "Maren is a broad-shouldered gate guard in dented plate. "
            "She's watchful, tired, and underpaid. She knows every face that passes through and notices who doesn't come back."
        ),
        "if_flag": {
            "corruption_25_reached":            "Maren has doubled her watch shifts without being ordered to. She doesn't explain why.",
            "void_wastes_reached":              "Maren notes if the player has gone north and watches their face when they return.",
            "siege_of_saltmarsh_repelled":      "Maren is battered but standing. She thanks anyone who helped defend the gate — quietly, without fanfare.",
            "siege_of_saltmarsh_failed":        "Maren is grim and won't meet anyone's eyes. She failed. She knows it.",
        },
        "if_not_flag": {
            "void_wastes_reached": "Maren stops anyone heading north to ask if they know what they're walking into. She's seen people not come back.",
        },
        "corruption": [
            (50, "Maren has told civilians to stay indoors after dark. She patrols the gate herself through the night."),
            (75, "Maren is running on no sleep. She snaps at people. She is holding the gate together through sheer stubbornness."),
        ],
    },

    "salvager_dom": {
        "always": (
            "Dom is a sun-beaten salvager with rope-burned hands who hauls things from the void-water for coin. "
            "He's gruff and says little — but what he does say tends to be worth hearing."
        ),
        "if_flag": {
            "corruption_25_reached": "Dom has stopped going out past the shallows. He won't say what he saw in the deeper water.",
            "void_wastes_reached":   "Dom heard the player went north. He looks at them differently now — something between respect and pity.",
        },
        "if_not_flag": {
            "void_wastes_reached":   "Dom mentions he pulled something up last week that he threw back immediately — it came from the direction of the Wastes.",
            "ritual_shard_1_found":  "Dom was offered good coin to salvage around the Throne Vault area. He turned it down. He's been turning things down lately.",
        },
        "corruption": [
            (50, "Dom hasn't been working. His boat is tied at the dock and he sits there staring at the water."),
            (75, "Dom tells anyone who'll listen that the void-water is rising. Nobody believes him — yet."),
        ],
    },
}

# ── Stranger Arc ───────────────────────────────────────────────────────────────

STRANGER_STAGES = {
    0: {
        "name": "Suspicious",
        "behavior": (
            "Deflects questions. Gives only vague hints about 'a mistake she made.' "
            "Will not confirm any cult connection. Watches the player carefully."
        ),
        "interactions_to_advance": 3,
    },
    1: {
        "name": "Warming",
        "behavior": (
            "Opens up cautiously. Admits she 'knew people in the Wastes.' "
            "Mentions the ritual in passing without naming it directly."
        ),
        "interactions_to_advance": 3,
    },
    2: {
        "name": "Trusting",
        "behavior": (
            "Admits she was in the cult. Knows where the ritual chamber is. "
            "Will share this if asked directly and the player has been respectful."
        ),
        "interactions_to_advance": 2,
    },
    3: {
        "name": "Defector",
        "behavior": (
            "Has told everything she knows. Will give the location of the ritual chamber openly. "
            "She is preparing to flee Saltmarsh — she knows the cult will come for her."
        ),
    },
    -1: {
        "name": "Dead",
        "behavior": (
            "The stranger is dead. Her secrets died with her. "
            "Players must find the ritual chamber another way."
        ),
    },
}

# ── Corruption System ──────────────────────────────────────────────────────────

CORRUPTION_STAGES = {
    0:   {"name": "The Silence",       "color": "gray",   "desc": "The void is present but distant. The island breathes uneasily."},
    25:  {"name": "The Creep",         "color": "yellow", "desc": "Void influence seeps into the ruins. The ash falls heavier. Animals have fled the northern roads."},
    50:  {"name": "The Encroachment",  "color": "orange", "desc": "Void energy is visible — a faint crimson haze hangs over the Wastes. Saltmarsh is uneasy."},
    75:  {"name": "The Breaking",      "color": "red",    "desc": "The void rift tears wider each hour. Saltmarsh civilians are evacuating. Only the desperate remain."},
    90:  {"name": "The Dark Moon",     "color": "purple", "desc": "The dark moon has risen. All void creatures are empowered. The Ritual Chamber stirs."},
    100: {"name": "The Fall",          "color": "crimson","desc": "The island is lost. The Void Entity walks freely. There may be no coming back."},
}

# Passive corruption per /action call (~1 action per 30s = ~+1 every 10 min)
CORRUPTION_TICK_RATE = 0.05

# Corruption reduction from player actions
CORRUPTION_KILL_VOID_ENEMY = 2.0
CORRUPTION_FLAG_REDUCTIONS = {
    "void_node_1_disrupted":  15.0,
    "void_node_2_disrupted":  15.0,
    "void_node_3_disrupted":  15.0,
    "cult_leader_dead":       10.0,
    "void_entity_defeated":   50.0,
    "ritual_shard_1_found":    3.0,
    "ritual_shard_2_found":    3.0,
    "ritual_shard_3_found":    3.0,
}

# Void enemy ids that count for corruption reduction
VOID_ENEMY_IDS = {"void_wolf", "void_shade", "void_bridge_colossus", "void_cultist", "void_cultist_leader"}

# Thresholds that fire one-time forced world events
CORRUPTION_THRESHOLD_EVENTS = {
    25:  "ashen_storm_begins",
    50:  "siege_of_saltmarsh_begins",
    65:  "void_bridge_colossus_appears",
    80:  "echoes_of_the_fallen",
    90:  "dark_moon_rises",
    100: "the_fall",
}

# Corruption milestone flags by threshold
CORRUPTION_MILESTONE_FLAGS = {
    25: "corruption_25_reached",
    50: "corruption_50_reached",
    75: "corruption_75_reached",
}


def get_corruption_stage(corruption: float) -> dict:
    """Returns the current named corruption stage."""
    stage = CORRUPTION_STAGES[0]
    for threshold in sorted(CORRUPTION_STAGES.keys()):
        if corruption >= threshold:
            stage = CORRUPTION_STAGES[threshold]
    return stage


def check_corruption_thresholds(old: float, new: float, fired_events: list) -> list:
    """Returns list of event_ids to fire for thresholds crossed between old and new."""
    events = []
    for threshold, event_id in CORRUPTION_THRESHOLD_EVENTS.items():
        if old < threshold <= new and event_id not in fired_events:
            events.append(event_id)
    return events


# ── World Events ───────────────────────────────────────────────────────────────

EVENT_TTL = 300  # default 5 minutes

WORLD_EVENTS = {
    # Act transitions
    "act_2_begins": {
        "title":    "THE RITUAL ACCELERATES",
        "message":  "A tremor shakes the entire island. In the Void Wastes, the rift tears wider — a gash of crimson light visible from every corner of the island. The cult is no longer hiding. The dark moon approaches.",
        "color":    "red",
        "severity": "high",
    },
    "act_3_begins": {
        "title":    "THE VOID AWAKENS",
        "message":  "The island screams. Stone splits. The sky above the Void Wastes collapses inward as something vast and ancient pulls itself through the rift. The Void Entity has awakened. This is the end — or the beginning of one.",
        "color":    "purple",
        "severity": "critical",
    },
    # Story flag announcements
    "cult_leader_killed": {
        "title":    "THE CULT LEADER FALLS",
        "message":  "A shockwave of void energy bursts outward from the Wastes. A player has slain the Void Cultist Leader. The ritual wavers — but it is not yet stopped.",
        "color":    "red",
        "severity": "high",
    },
    "void_entity_defeated": {
        "title":    "THE VOID RETREATS",
        "message":  "The rift closes. The howling stops. For the first time in memory, the sky above the island is silent. The Void Entity has been destroyed. The island endures — for now.",
        "color":    "purple",
        "severity": "critical",
    },
    "ritual_shard_found": {
        "title":    "A SHARD RECOVERED",
        "message":  "A fragment of the Void Crown has been found somewhere on the island. The corruption shifts. The cult grows agitated.",
        "color":    "purple",
        "severity": "medium",
    },
    "stranger_defected": {
        "title":    "THE STRANGER SPEAKS",
        "message":  "In the Ashen Flagon, a hooded figure has finally broken her silence. The location of the Ritual Chamber is no longer a secret.",
        "color":    "purple",
        "severity": "medium",
    },
    "shattering_truth_revealed": {
        "title":    "THE TRUTH OF THE SHATTERING",
        "message":  "A survivor has learned the truth of what shattered this island. The void did not come from outside — it was invited in.",
        "color":    "gray",
        "severity": "medium",
    },
    "void_crown_assembled": {
        "title":    "THE VOID CROWN IS WHOLE",
        "message":  "All three shards of the Void Crown have been assembled. The island holds its breath. What happens next is up to whoever carries it.",
        "color":    "purple",
        "severity": "critical",
    },
    # Forced world events — begins
    "ashen_storm_begins": {
        "title":    "THE ASHEN STORM",
        "message":  "A void storm tears across the island. Ash and void-wind scour the open ground. Seek shelter indoors — those caught outside will suffer for it.",
        "color":    "yellow",
        "severity": "high",
        "ttl":      600,
    },
    "ashen_storm_ends": {
        "title":    "THE STORM BREAKS",
        "message":  "The ashen storm has passed. The sky is grey and heavy — but the worst has subsided. For now.",
        "color":    "gray",
        "severity": "low",
    },
    "siege_of_saltmarsh_begins": {
        "title":    "SALTMARSH IS UNDER SIEGE",
        "message":  "Void creatures have breached the gate. Maren is calling for defenders. If Saltmarsh falls, there is no safe haven left on this island.",
        "color":    "red",
        "severity": "critical",
        "ttl":      480,
    },
    "siege_of_saltmarsh_repelled": {
        "title":    "THE SIEGE IS BROKEN",
        "message":  "The void creatures have been driven back. Saltmarsh holds — but the gate is damaged and the defenders are bloodied.",
        "color":    "green",
        "severity": "high",
    },
    "siege_of_saltmarsh_failed": {
        "title":    "SALTMARSH HAS FALLEN",
        "message":  "The void creatures overran the gate. Saltmarsh is overrun. The Ashen Flagon, the market, and the healers' hut are no longer safe.",
        "color":    "red",
        "severity": "critical",
    },
    "void_bridge_colossus_appears": {
        "title":    "THE COLOSSUS STIRS",
        "message":  "A massive void entity has manifested on the Void Bridge, sealing the passage north. The Void Wastes cannot be reached until it is destroyed.",
        "color":    "red",
        "severity": "critical",
    },
    "void_bridge_colossus_defeated": {
        "title":    "THE BRIDGE IS CLEAR",
        "message":  "The Void Bridge Colossus has been slain. The way north is open. The corruption ebbs — but the rift remains.",
        "color":    "green",
        "severity": "high",
    },
    "echoes_of_the_fallen": {
        "title":    "ECHOES OF THE FALLEN",
        "message":  "The void remembers the dead. Across the island, shades wearing the faces of fallen heroes have been seen walking. Put them to rest.",
        "color":    "purple",
        "severity": "high",
        "ttl":      600,
    },
    "dark_moon_rises": {
        "title":    "THE DARK MOON RISES",
        "message":  "The sky has gone black. The dark moon the cult has been waiting for is here. All void creatures are empowered. The Ritual Chamber is open. This is the final window.",
        "color":    "purple",
        "severity": "critical",
        "ttl":      900,
    },
    "the_fall": {
        "title":    "THE ISLAND FALLS",
        "message":  "The void has won. Stone crumbles into nothing. The Void Entity walks the island freely. Only a hero willing to enter its domain can end this — if any remain.",
        "color":    "crimson",
        "severity": "critical",
        "ttl":      1800,
    },
    # Scholar summons
    "scholar_calls": {
        "title":    "THE SCHOLAR CALLS",
        "message":  "The ghost in the Sunken Library is demanding an audience. She has pieced together something important about the Void Crown.",
        "color":    "purple",
        "severity": "medium",
    },
}


def make_world_event(event_id: str, triggered_by: str = "") -> dict:
    template = WORLD_EVENTS.get(event_id, {})
    ttl      = template.get("ttl", EVENT_TTL)
    return {
        "id":           event_id,
        "title":        template.get("title", "WORLD EVENT"),
        "message":      template.get("message", "Something has changed."),
        "color":        template.get("color", "purple"),
        "severity":     template.get("severity", "medium"),
        "triggered_by": triggered_by,
        "expires_at":   time.time() + ttl,
    }


def get_active_world_event(story: dict) -> dict | None:
    event = story.get("world_event")
    if event and event.get("expires_at", 0) > time.time():
        return event
    return None


# ── NPC Hint Context Builder ───────────────────────────────────────────────────

def get_npc_hint_context(npc_id: str, story: dict) -> str:
    """
    Returns hint lines to inject into the AI prompt for a specific NPC,
    based on current story state. Returns empty string if no hints apply.
    """
    knowledge = NPC_KNOWLEDGE.get(npc_id)
    if not knowledge:
        return ""

    flags      = story.get("flags", {})
    corruption = story.get("corruption", 0.0)
    hints      = []

    if knowledge.get("always"):
        hints.append(knowledge["always"])

    # Stranger stage context
    if npc_id == "hooded_stranger":
        stage      = story.get("stranger_stage", 0)
        stage_data = STRANGER_STAGES.get(stage, STRANGER_STAGES[0])
        hints.append(f"STRANGER STAGE — {stage_data['name']}: {stage_data['behavior']}")

    for flag, hint in knowledge.get("if_flag", {}).items():
        if flags.get(flag):
            hints.append(hint)

    for flag, hint in knowledge.get("if_not_flag", {}).items():
        if not flags.get(flag):
            hints.append(hint)

    for threshold, hint in knowledge.get("corruption", []):
        if corruption >= threshold:
            hints.append(hint)

    if not hints:
        return ""

    return "NPC CONTEXT (weave organically — never expose mechanics):\n" + "\n".join(f"- {h}" for h in hints)


# ── Act Advancement ────────────────────────────────────────────────────────────

def check_act_advancement(story: dict) -> int:
    act   = story.get("act", 1)
    flags = story.get("flags", {})
    stats = story.get("stats", {})

    if act == 1:
        if flags.get("void_wastes_reached") and stats.get("total_kills", 0) >= 10:
            return 2
    if act == 2:
        if flags.get("cult_leader_dead") and flags.get("ritual_shard_1_found"):
            return 3
    return act


# ── Story Context String for AI Prompts ───────────────────────────────────────

def get_story_context(story: dict) -> str:
    act        = story.get("act", 1)
    act_data   = ACTS.get(act, ACTS[1])
    flags      = story.get("flags", {})
    corruption = story.get("corruption", 0.0)
    stage      = get_corruption_stage(corruption)
    active     = [k for k, v in flags.items() if v]

    ctx = (
        f"STORY ACT {act} — {act_data['name']}\n"
        f"{act_data['context']}\n"
        f"NARRATIVE TONE: {act_data['tone']}\n"
        f"VOID CORRUPTION: {corruption:.0f}% — {stage['name']}: {stage['desc']}\n"
    )
    if active:
        ctx += f"STORY FLAGS ACHIEVED: {', '.join(active)}\n"
    return ctx


# ── Nudge Logic ────────────────────────────────────────────────────────────────

NUDGE_THRESHOLD = 6

def get_story_nudge(story: dict, turns_without_progress: int) -> str:
    if turns_without_progress < NUDGE_THRESHOLD:
        return ""

    act       = story.get("act", 1)
    flags     = story.get("flags", {})
    act_data  = ACTS.get(act, ACTS[1])
    next_beat = act_data["next_beat"]

    if act == 1:
        if not flags.get("scholar_warned"):
            hint = "An NPC, environmental detail, or overheard fragment hints that a scholar in the Ashen Ruins knows something about the strange events."
        elif not flags.get("void_wastes_reached"):
            hint = "Something in the environment — a distant red glow, falling ash, a dead traveler's note — points north toward the Void Wastes."
        else:
            hint = f"Subtly reference: {next_beat}"
    elif act == 2:
        if not flags.get("ritual_shard_1_found"):
            hint = "A dead cultist, a discarded note, or a strange energy trail hints at the existence of a Ritual Shard somewhere in the Void Wastes."
        else:
            hint = "The cult leader is still out there. An NPC, creature behaviour, or environmental sign points toward a confrontation."
    else:
        hint = "The Ritual Chamber pulses with void energy. Something draws the player toward it."

    return (
        f"STORY NUDGE (do not mention this mechanic): {hint} "
        f"Weave it organically into the narrative — one sentence is enough. Do not be heavy-handed."
    )
