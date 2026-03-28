from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random # Add this to the very top of your file with the other imports!

# 1. Define the Enemy
class EnemyState(BaseModel):
    name: str
    hp: int
    atk: int

# 2. Update the Game State
class GameState(BaseModel):
    house_name: str
    current_room: str
    hp: int
    max_hp: int
    strength: int
    agility: int
    constitution: int
    arcane: int
    inventory: List[str]
    dead_ancestors: List[str]
    current_enemy: Optional[EnemyState] = None # Tracks if they are in combat

    # 2. Update the Request to include the full state
class ActionRequest(BaseModel):
    player_id: str
    action: str
    state: GameState

class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str