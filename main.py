from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize App
app = FastAPI(title="Echoes of the Fallen")

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

# 4. Pydantic Models
class RegisterRequest(BaseModel):
    name: str
    race: str
    player_class: str

class ActionRequest(BaseModel):
    player_id: str
    action: str
    # Changed to Dict to seamlessly accept the complex new state without validation errors
    state: Dict[str, Any] 

# 5. Helpers
def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if "world_state" in path:
            return {"world_history": [], "races": {}, "classes": {}, "skill_definitions": {}, "players": {}}
        return {}
    except json.JSONDecodeError:
         raise HTTPException(status_code=500, detail=f"{path} is corrupted. Check your JSON syntax.")

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

@app.get("/health")
async def health_check():
    return {"message": "Echoes of the Fallen server is running."}

# 8. Core Game Loop
@app.post("/action")
async def handle_action(request: ActionRequest):
    world_state = load_json("world_state.json")
    map_data    = load_json("map.json")

    # Get player
    player = world_state["players"].get(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get location
    location_key = player["location"]
    current_location = map_data.get(location_key)
    if not current_location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Check for movement
    action_lower = request.action.lower()
    for exit_location in current_location.get("exits", []):
        if exit_location.replace("_", " ") in action_lower or exit_location in action_lower:
            player["location"] = exit_location
            current_location = map_data[exit_location]
            break

    # Build Gemini prompt
    prompt = f"""
You are a dark fantasy dungeon master for 'Echoes of the Fallen'.

    WORLD HISTORY: {world_state["world_history"]}
    CURRENT LOCATION: {current_location["description"]}
    LOCATION HISTORY: {current_location.get("history", [])}
    PLAYER NAME: {player["name"]}
    PLAYER CLASS: {player["class"]}
    PLAYER HP: {player["hp"]}/{player["max_hp"]}
    PLAYER INVENTORY: {player["inventory"]}
    PLAYER ACTION: {request.action}

    Respond with vivid narrative (2-3 sentences). Then on a new line write:
    VISUAL: [one sentence describing the scene for image generation]
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    narrative = response.text

    # Save updated world state
    world_state["players"][request.player_id] = player
    save_json("world_state.json", world_state)

    return {
        "text": narrative,
        "image_base64": "",
        "status": player["status"],
        "location": player["location"],
        "hp": player["hp"],
        "max_hp": player["max_hp"]
    }