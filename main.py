from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
# from google import genai # Uncomment once you pip install google-genai

# 1. Initialize the App
app = FastAPI(title="Scion of the Shattered Crown Engine")

# 2. CORS Configuration (Crucial for hackathons)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your local HTML file to hit this API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Pydantic Models (Data Validation)
# If the frontend forgets to send 'player_id', FastAPI automatically rejects it.
class ActionRequest(BaseModel):
    player_id: str
    action: str

# 4. API & State Setup
# os.environ["GEMINI_API_KEY"] = "your_key_here"
# client = genai.Client()

# 5. Core Game Loop Endpoint
@app.post("/action")
async def handle_action(request: ActionRequest):
    """
    Receives the player's action, updates the state, and triggers the AI models.
    """
    player = request.player_id
    user_input = request.action
    
    # TODO: Open world_state.json and find the player's current location
    # TODO: Load map.json to see what is in that room
    # TODO: Pass the room data + user_input to Gemini 1.5 Flash
    # TODO: Pass Gemini's visual description to Nano Banana
    
    # Dummy response to test your frontend connection right now
    return {
        "text": f"You are {player}. You tried to: '{user_input}'. The shattered void echoes.",
        "image_base64": "", 
        "status": "alive"
    }

# 6. Sanity Check Endpoint
@app.get("/")
async def health_check():
    return {"message": "The Shattered Crown server is running."}