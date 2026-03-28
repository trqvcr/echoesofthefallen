from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import random
from google import genai
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize App
app = FastAPI(title="Echoes of the Fallen")

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Gemini Client (Crash-proof)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key and api_key != "placeholder" else None

# 4. Pydantic Models (THIS IS WHAT WAS MISSING!)
class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str

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
    current_enemy: Optional[dict] = None

class ActionRequest(BaseModel):
    player_id: str
    action: str
    state: GameState

# 5. Helpers
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# 6. Serve HTML pages
@app.get("/")
async def serve_login():
    return FileResponse("login.html")

@app.get("/game")
async def serve_game():
    return FileResponse("index.html")

# 7. Health Check
@app.get("/health")
async def health_check():
    return {"message": "Echoes of the Fallen server is running."}

# 8. Registration Endpoint
@app.post("/register")
async def register_player(request: RegisterRequest):
    # Map the starting stats based on your new rules.json logic
    stats = {
        "ashen_knight": {"str": 8, "agi": 3, "con": 7, "arc": 2, "hp": 55},
        "void_drifter": {"str": 5, "agi": 9, "con": 4, "arc": 2, "hp": 40},
        "rune_scribe":  {"str": 2, "agi": 4, "con": 4, "arc": 10, "hp": 40},
        "void_ranger":  {"str": 3, "agi": 10, "con": 3, "arc": 4, "hp": 35}
    }
    
    selected = stats.get(request.player_class, stats["ashen_knight"])
    
    # Build the starting state
    initial_state = {
        "house_name": request.name,
        "current_room": "ashen_courtyard",
        "hp": selected["hp"],
        "max_hp": selected["hp"],
        "strength": selected["str"],
        "agility": selected["agi"],
        "constitution": selected["con"],
        "arcane": selected["arc"],
        "inventory": ["Rusted Sword"],
        "dead_ancestors": [],
        "current_enemy": None
    }
    
    return {
        "message": "Character forged in the void.",
        "player_id": request.name.lower().replace(" ", "_"),
        "hp": initial_state["hp"],
        "max_hp": initial_state["max_hp"],
        "state": initial_state
    }

# 9. Core Game Loop
@app.post("/action")
async def handle_action(request: ActionRequest):
    game_state = request.state
    action = request.action.lower()
    
    # 1. Load the Lore & Map
    try:
        with open("map.json", "r") as f:
            world_map = json.load(f)
        with open("rules.json", "r") as f:
            rules = json.load(f)
    except FileNotFoundError:
        return {"text": "System Error: The archives (JSON files) are missing.", "state": game_state.dict(), "status": "alive"}

    # 2. Get Current Location Data
    room_id = game_state.current_room if game_state.current_room in world_map else "ashen_courtyard"
    room = world_map[room_id]
    
    # 3. Simple Movement Logic
    if action.startswith("go ") or action.startswith("move "):
        target = action.replace("go ", "").replace("move ", "").strip().replace(" ", "_")
        if target in room.get("exits", []):
            game_state.current_room = target
            room = world_map[target]
            action = "looks around the new area."

    # 4. The Gemini DM Prompt
    prompt = f"""
    You are the Dungeon Master for a grimdark text RPG called 'Echoes of the Fallen'.
    The Shattering occurred 300 years ago, breaking the Void Crown.
    
    PLAYER INFO:
    House: {game_state.house_name}
    Stats: STR {game_state.strength}, AGI {game_state.agility}, CON {game_state.constitution}, ARC {game_state.arcane}
    HP: {game_state.hp}/{game_state.max_hp}
    Inventory: {', '.join(game_state.inventory)}
    
    CURRENT LOCATION: {room.get('name', 'Unknown')}
    Description: {room.get('description', 'A dark void.')}
    Available Exits: {', '.join(room.get('exits', []))}
    NPCs present: {', '.join([npc['name'] for npc in room.get('npcs', {}).values()])}
    Items on ground: {', '.join(room.get('items', []))}
    
    PLAYER ACTION: "{action}"
    
    INSTRUCTIONS:
    Write a 2-3 sentence atmospheric response describing the outcome of the player's action. 
    Be grim, descriptive, and do not break character. 
    If they attack an NPC or take an item, describe the physical struggle or the cold touch of the object.
    Do NOT offer a list of choices. Just tell them what happens.
    """

    # 5. Call Gemini 1.5 Flash
    if client:
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            response_text = response.text
        except Exception as e:
            response_text = f"The void ripples with an error: {str(e)}"
    else:
        response_text = "The AI is asleep. Set your GEMINI_API_KEY."

    # 6. Return Data to Frontend
    return {
        "text": response_text,
        "state": game_state.dict(),
        "location": room.get('name', 'Unknown'),
        "status": "alive"
    }