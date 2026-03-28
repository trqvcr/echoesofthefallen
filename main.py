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

# 3. Gemini Client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 4. Pydantic Models
class ActionRequest(BaseModel):
    player_id: str
    action: str

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

# 8. Core Game Loop
@app.post("/action")
async def handle_action(request: ActionRequest):
    world_state = load_json("world_state.json")
    map_data = load_json("map.json")

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