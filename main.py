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

# 2. CORS - Fixed Syntax
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Gemini Client (Safely handle missing key)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# 4. Pydantic Models - Fixed to match your Frontend
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
    state: GameState # Crucial for your save system!

# 5. Serve HTML pages
@app.get("/")
async def serve_login():
    return FileResponse("login.html")

@app.get("/game")
async def serve_game():
    return FileResponse("index.html")

# 6. Core Game Loop
@app.post("/action")
async def handle_action(request: ActionRequest):
    game_state = request.state
    action = request.action.lower()
    
    response_text = "The void echoes with your words, but nothing happens."
    
    # --- 1. TEST INVENTORY ---
    if "take" in action or "grab" in action:
        item = action.replace("take", "").replace("grab", "").strip()
        if item:
            game_state.inventory.append(item.title())
            response_text = f"You picked up the {item.title()}."
        else:
            response_text = "You grasp at the shadows."

    # --- 2. TEST COMBAT ---
    elif "attack" in action or "fight" in action:
        damage = random.randint(5, 15)
        game_state.hp -= damage
        
        if game_state.hp <= 0:
            game_state.hp = 0
            response_text = f"The shadows lash back for {damage} damage! You have fallen. Your lineage ends here..."
            return {
                "text": response_text,
                "state": game_state.dict(),
                "status": "dead"
            }
        else:
            response_text = f"You strike out, but the void strikes back for {damage} damage! You have {game_state.hp} HP left."

    # --- 3. TEST HEALING ---
    elif "heal" in action or "rest" in action:
        heal_amt = random.randint(10, 20)
        game_state.hp = min(game_state.max_hp, game_state.hp + heal_amt)
        response_text = f"You rest in the quiet dark, restoring {heal_amt} HP."

    # --- 4. TEST MOVEMENT ---
    elif "go" in action or "move" in action:
        direction = action.replace("go", "").replace("move", "").strip()
        new_location = direction.title() if direction else "Unknown"
        game_state.current_room = new_location
        response_text = f"You step cautiously into {new_location}."

    return {
        "text": response_text,
        "state": game_state.dict(),
        "location": game_state.current_room,
        "status": "alive"
    }

@app.post("/reset")
async def reset_game(request: ActionRequest):
    # Move current character name to 'dead_ancestors' before wiping
    state = request.state
    state.dead_ancestors.append(state.house_name)
    
    # Return a "Fresh" state but keep the dead ancestors list for Nano Banana
    new_state = {
        "house_name": state.house_name,
        "current_room": "ashen_courtyard",
        "hp": 55, "max_hp": 55,
        "strength": 8, "agility": 3, "constitution": 7, "arcane": 2,
        "inventory": ["Rusted Sword"],
        "dead_ancestors": state.dead_ancestors,
        "current_enemy": None
    }
    
    return {
        "text": "Your previous life fades into an echo. A new scion rises.",
        "state": new_state
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)