from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from google import genai 

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

# 4. Pydantic Models
class ActionRequest(BaseModel):
    player_id: str
    action: str
    current_room: str

# 5. Serve the Frontend (This makes it a true Web App)
@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

# 6. Core Game Loop Endpoint
@app.post("/action")
async def handle_action(request: ActionRequest):
    player = request.player_id
    action = request.action.lower()
    
    # Simple movement logic checking map.json
    room = world_map.get(request.current_room, {"name": "The Void", "description": "You are lost.", "exits": {}})
    new_room_key = request.current_room
    
    if "go " in action:
        direction = action.replace("go ", "").strip()
        if direction in room.get("exits", {}):
            new_room_key = room["exits"][direction]
            room = world_map[new_room_key]
    
    # TODO: Pass this room data to Gemini instead of hardcoding it!
    response_text = f"You move to {room.get('name', 'Unknown')}. {room.get('description', '')}"
    
    return {
        "text": response_text,
        "current_room": new_room_key,
        "image_base64": "", 
        "status": "alive"
    }