"""
One-time script: fix void_bridge exits in Supabase.
  - Replace 'saltmarsh_settlement' (region) with 'saltmarsh_gate' (location)
  - Add 'void_wastes_edge' exit
Run: python patch_exits.py
"""
from db import get_all_locations, save_location

locs = get_all_locations()
vb = locs.get("void_bridge")
if not vb:
    print("ERROR: void_bridge not found in DB")
    raise SystemExit(1)

old_exits = vb.get("exits", [])
print(f"Current void_bridge exits: {old_exits}")

new_exits = []
for e in old_exits:
    if e == "saltmarsh_settlement":
        new_exits.append("saltmarsh_gate")
    else:
        new_exits.append(e)
if "void_wastes_edge" not in new_exits:
    new_exits.append("void_wastes_edge")

vb["exits"] = new_exits
save_location("void_bridge", vb)
print(f"Updated void_bridge exits: {new_exits}")
