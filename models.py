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

class AvatarRequest(BaseModel):
    player_id: str
    description: str
    gender: str = "unspecified"

class TravelRequest(BaseModel):
    player_id: str
    destination: str

class SkillChoiceRequest(BaseModel):
    player_id: str
    skill_id:  str

class ForgeRequest(BaseModel):
    player_id:   str
    skill_ids:   list   # 1 or 2 skill ids to sacrifice
    description: str    # player's description of the new skill

class TTSRequest(BaseModel):
    text: str
