import hashlib
import os
from datetime import datetime, timezone
from fastapi import HTTPException
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Player ─────────────────────────────────────────────────────────────────────

def get_player(player_id: str) -> dict | None:
    res = sb.table("players").select("state").eq("id", player_id).execute()
    print(f"[get_player] id={player_id} data={res.data} count={res.count}")
    if res.data:
        return res.data[0]["state"]  # type: ignore
    return None


def save_player(player_id: str, state: dict):
    sb.table("players").upsert({
        "id":         player_id,
        "state":      state,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).execute()


# ── World & Locations ──────────────────────────────────────────────────────────

def get_world() -> dict:
    res = sb.table("world").select("data").eq("id", 1).execute()
    if res.data:
        return res.data[0]["data"]
    raise HTTPException(status_code=500, detail="World state not found in Supabase. Did you run migrate.py?")

def save_world(data: dict):
    sb.table("world").update({"data": data}).eq("id", 1).execute()

def get_all_locations() -> dict:
    res = sb.table("locations").select("key, data").execute()
    return {row["key"]: row["data"] for row in res.data}

def get_location(key: str) -> dict | None:
    res = sb.table("locations").select("data").eq("key", key).execute()
    if res.data and isinstance(res.data, list) and len(res.data) > 0:
        row = res.data[0]
        if isinstance(row, dict):
            data = row.get("data")
            return data if isinstance(data, dict) else None
    return None

def save_location(key: str, data: dict):
    sb.table("locations").upsert({"key": key, "data": data, "updated_at": datetime.now(timezone.utc).isoformat()}).execute()


# ── Auth ───────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
