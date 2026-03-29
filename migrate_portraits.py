"""
One-time migration: convert base64 portrait strings in Supabase DB to Storage URLs.

Touches:
  - players.state.avatar_portrait
  - locations.data.npcs.*.portrait
  - locations.data.reference_image

Run once:  python migrate_portraits.py
Safe to re-run — skips anything that's already a URL.
"""

import base64
from db import sb, upload_image


def is_base64_image(value: str) -> bool:
    return isinstance(value, str) and value.startswith("data:image")


def decode_b64(value: str) -> bytes | None:
    try:
        data = value.split(",", 1)[-1] if "," in value else value
        return base64.b64decode(data)
    except Exception:
        return None


def migrate_players():
    print("── Players ──────────────────────────────────")
    rows = sb.table("players").select("id, state").execute().data
    for row in rows:
        player_id = row["id"]
        state     = row["state"]
        portrait  = state.get("avatar_portrait", "")

        if not is_base64_image(portrait):
            print(f"  {player_id}: skip (already URL or empty)")
            continue

        img_bytes = decode_b64(portrait)
        if not img_bytes:
            print(f"  {player_id}: skip (decode failed)")
            continue

        try:
            url = upload_image(f"avatars/{player_id}.jpg", img_bytes)
            state["avatar_portrait"] = url
            sb.table("players").update({"state": state}).eq("id", player_id).execute()
            print(f"  {player_id}: ✓ {url}")
        except Exception as e:
            print(f"  {player_id}: ERROR — {e}")


def migrate_locations():
    print("── Locations ────────────────────────────────")
    rows = sb.table("locations").select("key, data").execute().data
    for row in rows:
        key      = row["key"]
        data     = row["data"]
        dirty    = False

        # NPC portraits
        for npc_id, npc in data.get("npcs", {}).items():
            portrait = npc.get("portrait", "")
            if not is_base64_image(portrait):
                continue
            img_bytes = decode_b64(portrait)
            if not img_bytes:
                continue
            try:
                url = upload_image(f"npcs/{npc_id}.jpg", img_bytes)
                data["npcs"][npc_id]["portrait"] = url
                dirty = True
                print(f"  {key}/{npc_id}: ✓ {url}")
            except Exception as e:
                print(f"  {key}/{npc_id}: ERROR — {e}")

        # Reference image
        ref = data.get("reference_image", "")
        if is_base64_image(ref):
            img_bytes = decode_b64(ref)
            if img_bytes:
                try:
                    url = upload_image(f"scenes/{key}.jpg", img_bytes)
                    data["reference_image"] = url
                    dirty = True
                    print(f"  {key}/reference_image: ✓ {url}")
                except Exception as e:
                    print(f"  {key}/reference_image: ERROR — {e}")

        if dirty:
            sb.table("locations").update({"data": data}).eq("key", key).execute()


if __name__ == "__main__":
    migrate_players()
    migrate_locations()
    print("\nDone.")
