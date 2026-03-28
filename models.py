from pydantic import BaseModel
from typing import Dict, Any, Optional

class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str

class ActionRequest(BaseModel):
    player_id: str
    action: str
    state: Optional[Dict[str, Any]] = None