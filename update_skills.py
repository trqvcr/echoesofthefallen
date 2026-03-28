"""
update_skills.py - Run once to migrate skill_definitions to structured format
and add advanced skills + class_skill_pools to world data.
"""
from db import get_world, save_world
import json

UPDATED_SKILLS = {
    "shield_bash": {
        "name": "Shield Bash",
        "description": "Slam your shield into an enemy, dealing damage and stunning them briefly.",
        "base_damage": 4, "scales_with": "STR",
        "mana_cost": 0, "stamina_cost": 1, "cooldown_turns": 3,
        "effect": "stun", "effect_value": 1, "effect_duration": 1,
    },
    "iron_stance": {
        "name": "Iron Stance",
        "description": "Plant your feet and brace for impact, reducing incoming damage this turn.",
        "base_damage": 0, "scales_with": "CON",
        "mana_cost": 0, "stamina_cost": 1, "cooldown_turns": 3,
        "effect": "block", "effect_value": 50, "effect_duration": 1,
    },
    "poison_blade": {
        "name": "Poison Blade",
        "description": "Coat your weapon in void-touched poison, dealing damage over time.",
        "base_damage": 3, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 1, "cooldown_turns": 4,
        "effect": "poison", "effect_value": 2, "effect_duration": 3,
    },
    "shadow_step": {
        "name": "Shadow Step",
        "description": "Melt into the shadows and reappear behind your target for a backstab.",
        "base_damage": 6, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 2, "cooldown_turns": 3,
        "effect": "expose", "effect_value": 4, "effect_duration": 1,
    },
    "void_shot": {
        "name": "Void Shot",
        "description": "Fire an arrow charged with Void energy that bleeds the target.",
        "base_damage": 7, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 1, "cooldown_turns": 3,
        "effect": "bleed", "effect_value": 2, "effect_duration": 2,
    },
    "hunters_eye": {
        "name": "Hunter's Eye",
        "description": "Study your target, identifying a weakness that amplifies your next strike.",
        "base_damage": 0, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 1, "cooldown_turns": 2,
        "effect": "crit", "effect_value": 4, "effect_duration": 1,
    },
    "void_bolt": {
        "name": "Void Bolt",
        "description": "Fire a concentrated bolt of Void energy that saps the target's strength.",
        "base_damage": 8, "scales_with": "ARC",
        "mana_cost": 2, "stamina_cost": 0, "cooldown_turns": 3,
        "effect": "weaken", "effect_value": 2, "effect_duration": 2,
    },
    "rune_ward": {
        "name": "Rune Ward",
        "description": "Inscribe a protective rune that absorbs incoming damage.",
        "base_damage": 0, "scales_with": "ARC",
        "mana_cost": 2, "stamina_cost": 0, "cooldown_turns": 4,
        "effect": "shield", "effect_value": 10, "effect_duration": 3,
    },
    "arcane_sight": {
        "name": "Arcane Sight",
        "description": "Open your mind to the Void, exposing enemy weaknesses.",
        "base_damage": 0, "scales_with": "ARC",
        "mana_cost": 1, "stamina_cost": 0, "cooldown_turns": 5,
        "effect": "expose", "effect_value": 3, "effect_duration": 2,
    },
    # ashen_knight advanced
    "void_cleave": {
        "name": "Void Cleave",
        "description": "Channel void energy through your blade in a sweeping cleave that bleeds the target.",
        "base_damage": 6, "scales_with": "STR",
        "mana_cost": 1, "stamina_cost": 2, "cooldown_turns": 4,
        "effect": "bleed", "effect_value": 2, "effect_duration": 2,
    },
    "bulwark": {
        "name": "Bulwark",
        "description": "Raise a void-reinforced barrier, absorbing a large amount of incoming damage.",
        "base_damage": 0, "scales_with": "CON",
        "mana_cost": 0, "stamina_cost": 2, "cooldown_turns": 5,
        "effect": "shield", "effect_value": 15, "effect_duration": 3,
    },
    "warcry": {
        "name": "Warcry",
        "description": "A thunderous warcry that shatters your enemy's resolve and lowers their attack.",
        "base_damage": 0, "scales_with": "STR",
        "mana_cost": 0, "stamina_cost": 1, "cooldown_turns": 4,
        "effect": "weaken", "effect_value": 3, "effect_duration": 3,
    },
    # void_drifter advanced
    "backstab": {
        "name": "Backstab",
        "description": "A precision strike from the blind spot, bypassing armor completely.",
        "base_damage": 10, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 2, "cooldown_turns": 4,
        "effect": "expose", "effect_value": 6, "effect_duration": 1,
    },
    "smoke_veil": {
        "name": "Smoke Veil",
        "description": "Vanish into a cloud of void smoke, dramatically boosting evasion.",
        "base_damage": 0, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 2, "cooldown_turns": 5,
        "effect": "dodge", "effect_value": 40, "effect_duration": 2,
    },
    "toxic_strike": {
        "name": "Toxic Strike",
        "description": "A heavy blow coated in concentrated void toxin that lingers for several turns.",
        "base_damage": 5, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 2, "cooldown_turns": 4,
        "effect": "poison", "effect_value": 4, "effect_duration": 3,
    },
    # void_ranger advanced
    "piercing_shot": {
        "name": "Piercing Shot",
        "description": "A focused shot that punches through armor plating.",
        "base_damage": 9, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 2, "cooldown_turns": 3,
        "effect": "expose", "effect_value": 5, "effect_duration": 1,
    },
    "multishot": {
        "name": "Multishot",
        "description": "Loose three void-charged arrows in rapid succession.",
        "base_damage": 5, "scales_with": "AGI",
        "mana_cost": 0, "stamina_cost": 2, "cooldown_turns": 4,
        "effect": "bleed", "effect_value": 3, "effect_duration": 2,
    },
    "void_trap": {
        "name": "Void Trap",
        "description": "Set a void-energy snare that immobilizes the enemy for several turns.",
        "base_damage": 0, "scales_with": "ARC",
        "mana_cost": 1, "stamina_cost": 1, "cooldown_turns": 6,
        "effect": "stun", "effect_value": 0, "effect_duration": 2,
    },
    # rune_scribe advanced
    "chain_bolt": {
        "name": "Chain Bolt",
        "description": "A void bolt that chains corrosive energy, severely weakening the target.",
        "base_damage": 6, "scales_with": "ARC",
        "mana_cost": 3, "stamina_cost": 0, "cooldown_turns": 4,
        "effect": "weaken", "effect_value": 4, "effect_duration": 3,
    },
    "void_prison": {
        "name": "Void Prison",
        "description": "Trap an enemy in a cage of void energy, locking them in place.",
        "base_damage": 0, "scales_with": "ARC",
        "mana_cost": 4, "stamina_cost": 0, "cooldown_turns": 6,
        "effect": "stun", "effect_value": 0, "effect_duration": 2,
    },
    "mana_surge": {
        "name": "Mana Surge",
        "description": "Channel all arcane power into a devastating void explosion.",
        "base_damage": 12, "scales_with": "ARC",
        "mana_cost": 5, "stamina_cost": 0, "cooldown_turns": 5,
        "effect": "none", "effect_value": 0, "effect_duration": 0,
    },
}

CLASS_SKILL_POOLS = {
    "ashen_knight": {
        "starting": ["shield_bash", "iron_stance"],
        "advanced":  ["void_cleave", "bulwark", "warcry"],
    },
    "void_drifter": {
        "starting": ["poison_blade", "shadow_step"],
        "advanced":  ["backstab", "smoke_veil", "toxic_strike"],
    },
    "void_ranger": {
        "starting": ["void_shot", "hunters_eye"],
        "advanced":  ["piercing_shot", "multishot", "void_trap"],
    },
    "rune_scribe": {
        "starting": ["void_bolt", "rune_ward", "arcane_sight"],
        "advanced":  ["chain_bolt", "void_prison", "mana_surge"],
    },
}

if __name__ == "__main__":
    world = get_world()
    world["skill_definitions"] = UPDATED_SKILLS
    world["class_skill_pools"]  = CLASS_SKILL_POOLS
    save_world(world)
    print(f"Updated {len(UPDATED_SKILLS)} skill definitions.")
    print(f"Added class_skill_pools for {list(CLASS_SKILL_POOLS.keys())}.")
    print("Done.")
