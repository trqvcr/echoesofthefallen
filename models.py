from pydantic import BaseModel
from typing import Dict, Any, Optional


class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str
    password: str


class LoginRequest(BaseModel):
    name: str
    password: str


class ActionRequest(BaseModel):
    player_id: str
    action: str
    state: Optional[Dict[str, Any]] = None

class RiseRequest(BaseModel):
    player_id: str
    heir_name: str
