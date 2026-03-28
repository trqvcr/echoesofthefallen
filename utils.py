import json
from fastapi import HTTPException


def load_json(path: str):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if "world_state" in path:
            return {"world_history": [], "races": {}, "classes": {}, "skill_definitions": {}}
        if "saves" in path:
            return {}
        return {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"{path} is corrupted. Check your JSON syntax.")


def save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
