from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from pydantic import BaseModel
from models import EnemyState, GameState, ActionRequest
import os
import json
from dotenv import load_dotenv
from google import genai 
from typing import List, Dict, Any

# 1. Load Environment Variables safely
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Client
# The client automatically looks for the GEMINI_API_KEY environment variable
if API_KEY:
    client = genai.Client()
else:
    print("WARNING: GEMINI_API_KEY not found in .env file!")
    client = None

# 2. Initialize the App
app = FastAPI(title="Echoes of the Fallen Engine")

# 3. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the map data
try:
    with open("map.json", "r") as f:
        world_map = json.load(f)
except FileNotFoundError:
    world_map = {}
    print("WARNING: map.json not found!")

# 5. Serve the Frontend (Crucial for the Web App to load!)
@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.post("/action")
async def handle_action(request: ActionRequest):
    game_state = request.state
    action = request.action.lower()
    
    # --- COMBAT LOGIC ---
    if "attack" in action:
        # If no enemy exists, spawn a dummy goblin for testing
        if not game_state.current_enemy:
            game_state.current_enemy = EnemyState(name="Void Goblin", hp=15, atk=3)
            return {
                "text": "A snarling Void Goblin leaps from the shadows! Type 'attack' again to strike.",
                "state": game_state.dict(),
                "image_base64": "",
                "status": "alive"
            }

        # The Math: Player Damage = STR + 1d6 roll
        enemy = game_state.current_enemy
        player_dmg = game_state.strength + random.randint(1, 6)
        enemy.hp -= player_dmg
        
        battle_log = f"You strike the {enemy.name} for {player_dmg} damage! "

        # Check if enemy died
        if enemy.hp <= 0:
            battle_log += f"The {enemy.name} crumbles into dust. You are victorious!"
            game_state.current_enemy = None # Clear the enemy from the room
        else:
            # Enemy retaliates: Damage = ATK + 1d3 roll
            enemy_dmg = enemy.atk + random.randint(1, 3)
            # Subtract Agility (Dodge/Block mitigation)
            actual_dmg = max(1, enemy_dmg - (game_state.agility // 2)) 
            game_state.hp -= actual_dmg
            
            battle_log += f"The {enemy.name} slashes back for {actual_dmg} damage! It has {enemy.hp} HP left. "

        # Check for player death
        status = "alive"
        if game_state.hp <= 0:
            battle_log += "You fall to the ground. Your lineage ends here..."
            status = "dead"

        return {
            "text": battle_log,
            "state": game_state.dict(),
            "image_base64": "",
            "status": status
        }
    # --- END COMBAT LOGIC ---

    # 1. Movement Logic
    room = world_map.get(game_state.current_room, {"name": "The Void", "description": "You are lost.", "exits": {}})
    
    if "go " in action:
        direction = action.replace("go ", "").strip()
        if direction in room.get("exits", {}):
            game_state.current_room = room["exits"][direction]
            room = world_map[game_state.current_room]
    
    # 2. The Gemini Prompt
    # We feed the AI the current game state, the room description, and the user's action
    prompt = f"""
    You are the Dungeon Master for a dark fantasy text adventure called 'Echoes of the Fallen'.
    The player is the current scion of {game_state.house_name}.
    They have {game_state.hp} HP.
    
    They are currently in: {room.get('name')}
    Room description: {room.get('description')}
    
    The player attempts to: '{action}'
    
    Describe what happens next in 2 to 3 short, atmospheric sentences. 
    Keep it grim, mysterious, and engaging. Do NOT let them easily escape danger.
    """
    
    # 3. Call the Gemini API
    if client:
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
            )
            response_text = response.text
        except Exception as e:
            response_text = f"[System Error: The AI is sleeping. {str(e)}]"
    else:
        # Fallback if the API key isn't loaded properly
        response_text = f"You are in {room.get('name')}. You tried to '{action}', but the AI API key is missing!"
    
    # 4. Return the AI's story and the updated state to the frontend
    return {
        "text": response_text,
        "state": game_state.dict(),
        "image_base64": "", 
        "status": "alive"
    }