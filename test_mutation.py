"""
Quick mutation tester. Make sure uvicorn is running first:
    uvicorn main:app --reload
"""
import requests
import json

BASE = "http://localhost:8001"
PLAYER = "mutation_test"
PASSWORD = "test1234"


def pp(label, data):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print('='*50)
    print(json.dumps(data, indent=2))


# ── Setup: always fresh — delete via Supabase before running if player exists ──
# Run this SQL first if you get stuck in combat:
#   DELETE FROM players WHERE id = 'mutation_test';
r = requests.post(f"{BASE}/register", json={
    "name": PLAYER, "race": "human", "player_class": "ashen_knight", "password": PASSWORD
})
if r.status_code == 200:
    print(f"[+] Registered '{PLAYER}'")
    player_id = r.json()["player_id"]
elif "already taken" in r.text:
    r = requests.post(f"{BASE}/login", json={"name": PLAYER, "password": PASSWORD})
    print(f"[+] Logged in as '{PLAYER}'")
    player_id = r.json()["player_id"]
else:
    print(f"[!] Register failed: {r.text}")
    exit(1)


def action(text):
    r = requests.post(f"{BASE}/action", json={"player_id": player_id, "action": text})
    data = r.json()
    print(f"\n>>> ACTION: {text}")
    print(f"    NARRATIVE: {data.get('text','')[:200]}")
    state = data.get("state", {})
    print(f"    HP: {state.get('hp')}/{state.get('max_hp')} | Location: {data.get('location')}")
    return data


# ── Tests ──────────────────────────────────────────────────────────────────────

print("\n[TEST 1] Trivial action — should produce no state changes")
action("I look around the courtyard")

print("\n[TEST 2] Physical damage to environment — should produce staged state entry")
action("I smash my fist into the crumbling stone fountain as hard as I can")

print("\n[TEST 3] Permanent mark — should produce permanent state entry")
action("I carve my name into the wall with my sword")

print("\n[TEST 4] Another physical action — should produce state entry")
action("I kick over the dead soldier and take his broken sword")

print("\n[TEST 5] Trivial action — should produce NO state changes")
action("I look up at the sky")

print("\n[DONE] Check the server console for === MUTATION === output")
print("Then run this SQL to inspect the ashen_courtyard state:")
print("  SELECT data->'state' FROM locations WHERE key = 'ashen_courtyard';")
print("And this for the tavern:")
print("  SELECT data->'state', data->'npcs'->'osric'->'disposition' FROM locations WHERE key = 'the_ashen_flagon';")
