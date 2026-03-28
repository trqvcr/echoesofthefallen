"""
lore.py — Location-embedded lore entries that collectively tell the story of The Shattering.

THE OVERARCHING STORY:
  300 years ago, King Aldros Vael of Valdris Island attempted to cheat death using a forbidden
  void ritual. He believed crystallised void energy — a Ritual Shard — could anchor a rift open
  long enough to extract the essence of immortality. His court mage Serath warned him repeatedly.
  Aldros performed the ritual on the night of the Dark Moon alignment.

  The Shard shattered into seven pieces. The void rift tore open. Aldros was not made immortal —
  he was consumed and transformed into the Void Entity: a being of pure entropic will that exists
  between worlds. The island was devastated in an event survivors call "The Shattering."

  Now, 300 years later, a cult called "The Awakened" has been quietly collecting the scattered
  Ritual Shards. They believe releasing the Void Entity fully will "unmake death" and return
  everyone killed in the Shattering. They are wrong. The Entity wants only to unmake everything.

Each lore entry is a fragment. No single location tells the whole story.
"""

# ── Lore Entry Structure ──────────────────────────────────────────────────────
# Each entry:
#   id          — unique snake_case identifier
#   title       — display name shown in journal
#   source      — what object/thing contains it (book, inscription, letter, etc.)
#   trigger     — how it's found: "search", "read", "examine", "listen"
#   content     — the actual lore text shown to player
#   hint        — what the AI should describe when the player is near this lore
#                 (injected into prompt; never shown directly to player)

LOCATION_LORE: dict[str, list[dict]] = {

    "the_ashen_flagon": [
        {
            "id":      "innkeepers_account",
            "title":   "The Innkeeper's Account",
            "source":  "a worn journal behind the bar, spine cracked with age",
            "trigger": "search",
            "content": (
                "My father wrote this the morning after the Shattering. He never spoke of it. "
                "I found it in the walls when I took over the Flagon.\n\n"
                "'The sky split at midnight — not lightning, something slower. A seam, like cloth "
                "tearing. The ground shook for six hours without stopping. When dawn came, half the "
                "city was ash. The other half was us. I served drinks all day. No one paid. "
                "No one spoke. We just needed somewhere to be.'"
            ),
            "hint": "Behind the bar, wedged between bottles, a cracked journal spine is barely visible.",
        },
        {
            "id":      "last_rounds_ledger",
            "title":   "The Last Rounds",
            "source":  "a bar ledger from 300 years ago, still under the counter",
            "trigger": "examine",
            "content": (
                "A drink ledger, columns of names and tallies. The last page:\n\n"
                "'Third evening of the Dark Moon week. Thirty-two patrons at peak. "
                "Ran low on ash-mead. Must order more.\n"
                "Fourth evening. Twelve patrons. Several spoke of lights in the north. "
                "Soldiers marching toward the keep.\n"
                "Fifth evening — no one came tonight. The sky is wrong. "
                "Closing early. Something is wrong with the sky.'\n\n"
                "The ledger ends there. The rest of the pages are blank."
            ),
            "hint": "An old ledger sits beneath the bar counter, its final entries barely legible.",
        },
    ],

    "sunken_library": [
        {
            "id":      "void_nature_tome",
            "title":   "On the Nature of the Void",
            "source":  "a waterlogged scholarly tome on the eastern shelf",
            "trigger": "search",
            "content": (
                "Author unknown. Most pages dissolved. A readable passage:\n\n"
                "'...the Void is not darkness. Darkness is the absence of light. "
                "The Void is the absence of existence itself. To open a rift is not to "
                "make a door — it is to unmake the wall. What passes through does not travel. "
                "It simply ceases to be here and begins to be there, changed by the passage "
                "in ways that cannot be undone.\n"
                "Any ritual that uses a Void Shard as an anchor is not anchoring the rift. "
                "It is feeding the rift. The Shard is the bait. The rift is the mouth. "
                "Whoever proposed this to the King is either a fool or his enemy.'"
            ),
            "hint": "A swollen tome on the eastern shelf has survived despite the flooding — its cover is stamped with the royal seal.",
        },
        {
            "id":      "kings_commission",
            "title":   "The King's Library Commission",
            "source":  "an acquisition manifest nailed to the librarian's desk",
            "trigger": "examine",
            "content": (
                "Royal Library Acquisition Order — Sealed by King Aldros Vael:\n\n"
                "'By order of the Crown, all texts relating to the following subjects are to be "
                "collected, copied, and delivered to the throne study within fourteen days:\n"
                "— Void binding and void anchoring\n"
                "— The properties of crystallised void matter\n"
                "— Rituals of life extension, soul preservation, death inversion\n"
                "— Any records of previous void contact events\n\n"
                "Librarian Ossa's note, written in the margin in shaking hand: "
                "'I gave him everything. I should have burned it instead. I am so sorry.'"
            ),
            "hint": "A document is nailed to the librarian's sunken desk, its royal seal still legible beneath the waterline.",
        },
    ],

    "ash_burial_grounds": [
        {
            "id":      "burial_register",
            "title":   "The Burial Register",
            "source":  "a stone register carved into the entrance arch",
            "trigger": "examine",
            "content": (
                "Thousands of names carved in columns. The cause-of-death column uses shorthand:\n\n"
                "V.T. — Void-Taken (body not recovered)\n"
                "A.L. — Ash-Lung (suffocated in the ashfall)\n"
                "T.F. — The Fall (ground collapse)\n"
                "U.K. — Unknown\n\n"
                "Of 4,200 names, 3,847 are marked V.T.\n"
                "The last name carved is 'Serath, Court Mage.' "
                "His cause of death is left blank. Someone scratched it out."
            ),
            "hint": "The burial arch is carved floor to ceiling with names. One has been scratched out near the bottom.",
        },
        {
            "id":      "childs_grave",
            "title":   "A Child's Grave Marker",
            "source":  "a small stone marker in the western corner, hand-carved clumsily",
            "trigger": "search",
            "content": (
                "The stone is rough, carved by an amateur hand. It reads:\n\n"
                "'Lenne. Seven years. She was not taken by the void.\n"
                "She was taken by the King.\n"
                "Remember his name: Aldros Vael.\n"
                "Remember what he wanted.\n"
                "Remember what it cost.'"
            ),
            "hint": "In the far corner, a small grave marker sits apart from the others, its inscription facing away from the arch.",
        },
    ],

    "old_barracks": [
        {
            "id":      "last_orders",
            "title":   "Captain Veyne's Last Orders",
            "source":  "a military dispatch pinned to the command board",
            "trigger": "examine",
            "content": (
                "URGENT — All Saltmarsh Guard, issued by Captain Veyne, Third Watch:\n\n"
                "'Hold the southern gate. Do not let the void-touched through — "
                "they were people once but they are not people now. "
                "Do not engage the creatures from the north. Fall back. Hold the line.\n\n"
                "The King has performed the ritual. I do not know what he was promised. "
                "I know what it has cost us. "
                "Guard your posts. Guard each other. Forget the Crown.\n"
                "— Veyne'\n\n"
                "Beneath it, a later note in different handwriting: "
                "'Veyne held the gate for eleven days. We buried what we could find of him on the twelfth.'"
            ),
            "hint": "A command board still hangs on the wall, a dispatch pinned to it by a rusted knife.",
        },
        {
            "id":      "soldiers_letter",
            "title":   "An Unsent Letter",
            "source":  "a folded letter inside a rotted bunk, still sealed",
            "trigger": "search",
            "content": (
                "'Mother,\n"
                "I am writing this because I may not come back and I want someone to know what we saw.\n\n"
                "Three weeks ago the King's men came through and took half our unit north. "
                "They said it was for a royal ceremony. We were there to guard the perimeter.\n"
                "We were not told what the ceremony was.\n\n"
                "The mage — the one who serves the King — he was crying. "
                "I saw him through the tent flap. A grown man, weeping into his hands. "
                "That was the moment I knew it was wrong.\n\n"
                "When the sky split, four of my unit ran toward it. "
                "They did not come back. What came back was not them.\n"
                "I am holding the gate now. I don't know if anyone will read this.\n"
                "I love you. I loved all of you.\n— Thom'"
            ),
            "hint": "Inside one of the rotted bunks, something white catches the light — a folded letter, still sealed.",
        },
    ],

    "throne_vault": [
        {
            "id":      "kings_journal",
            "title":   "The King's Journal — Final Entry",
            "source":  "a leather-bound journal on the throne's armrest, perfectly preserved",
            "trigger": "examine",
            "content": (
                "The handwriting is precise. Confident. No fear.\n\n"
                "'Tonight is the Dark Moon alignment — the only night in a century when the "
                "void's membrane thins enough to anchor a rift with a single Shard. "
                "Serath has refused to assist. He will be dealt with afterward.\n\n"
                "I have studied this for nineteen years. I have read every text, spoken to every "
                "scholar, sacrificed every comfort. Death has taken my father, my wife, my son. "
                "It will not take me.\n\n"
                "The Shard is prepared. The circle is drawn. When I emerge from the void, "
                "I will be the first king in history to reign without end. "
                "Valdris will be eternal. I will be eternal.\n\n"
                "Let them call me mad. Let them call me wrong.\n"
                "They will call me immortal.\n\n"
                "— Aldros Vael, King of Valdris, last mortal night'"
            ),
            "hint": "A journal rests on the arm of the throne as though its owner stepped away for a moment and will return.",
        },
        {
            "id":      "seraths_warning",
            "title":   "Serath's Final Warning",
            "source":  "a letter slid under the vault door, never opened",
            "trigger": "search",
            "content": (
                "'Your Majesty,\n\n"
                "I have served you for thirty-one years. I have never refused a command "
                "until tonight. I am refusing this one.\n\n"
                "The texts you've read were written by men who never attempted this ritual "
                "because they understood what it actually does. A Void Shard does not anchor "
                "a rift. It attracts the void. You are not opening a door — "
                "you are ringing a bell in the dark and waiting to see what answers.\n\n"
                "Whatever answers will not grant immortality. "
                "It will consume you and wear your face.\n\n"
                "Please. The Shard can be destroyed. The ritual can be stopped. "
                "You have lost people you loved. So have I. Death is not the enemy. "
                "What you are about to unleash is.\n\n"
                "I am begging you as your friend.\n— Serath'"
            ),
            "hint": "A letter lies on the floor just inside the vault door, its seal unbroken — never opened.",
        },
    ],

    "void_bridge": [
        {
            "id":      "anchor_inscription",
            "title":   "The Anchor Runes",
            "source":  "runes carved into the bridge's central stones, older than the bridge itself",
            "trigger": "examine",
            "content": (
                "The runes are not decorative. A scholar's translation is scratched beside them:\n\n"
                "'BINDING WARD — Third Ring. Place at every rift approach. "
                "Renew on each Dark Moon. Do not let the wards fail.\n\n"
                "If the wards fail: do not approach. Do not look into the rift. "
                "Do not attempt to close it from this side. "
                "The ward does not keep the void out. "
                "The ward keeps what is inside the void from remembering you are here.'\n\n"
                "The runes are cracked. Some are missing entirely. "
                "The ward has been broken for a very long time."
            ),
            "hint": "The bridge's central stones are carved with runes — not for decoration. A hasty translation is scratched next to them.",
        },
        {
            "id":      "cultist_prayer",
            "title":   "A Cultist's Carving",
            "source":  "fresh markings carved over the old runes, still pale against the dark stone",
            "trigger": "search",
            "content": (
                "Carved recently — the stone chips are still fresh.\n\n"
                "'HE REMEMBERS US.\n"
                "WE ARE THE RETURNED.\n"
                "THE SHARDS WILL BE WHOLE.\n"
                "THE RIFT WILL BE OPEN.\n"
                "THE FALLEN WILL RISE.\n\n"
                "Below this, a symbol — a circle with a crack through it, "
                "the same symbol seen on the void altar.\n\n"
                "And below that, in smaller, less certain letters, as if added by someone else:\n"
                "'I don't think he remembers us the way they say. "
                "I don't think he remembers us at all.'"
            ),
            "hint": "Fresh chisel marks on the bridge railing — someone carved something here recently, over the older stonework.",
        },
    ],

    "ruined_keep": [
        {
            "id":      "final_stand_carving",
            "title":   "The Final Stand",
            "source":  "a commemorative carving on the keep's inner wall, clearly made years after the Shattering",
            "trigger": "examine",
            "content": (
                "'HERE THE GARRISON OF SALTMARSH HELD FOR ELEVEN DAYS.\n"
                "AGAINST WHAT CAME THROUGH THE RIFT WHEN THE KING BROKE THE WORLD.\n\n"
                "They had no orders. They had no hope of victory. "
                "They fought so that the living could run.\n\n"
                "Thirty-seven soldiers. Eleven days. "
                "The rift creatures did not pass this line.\n\n"
                "WE REMEMBER THEIR NAMES:\n"
                "Veyne. Dara. Ossian. Luth. Mira. Cael. Tomas. Pieret. Yann. Brek. Sessa. "
                "Dwyn. Fael. Ollan. Rosse. Teven. Corra. Baine. Niall. Fen. Leva. Kern. "
                "Solan. Deis. Maret. Cass. Idris. Bael. Orla. Yeva. Corin. Shan. Tas. "
                "Rowan. Ulv. Feye. Merren.\n\n"
                "THIRTY-SEVEN. ELEVEN DAYS. THEY HELD.'"
            ),
            "hint": "One wall of the keep is carved floor to ceiling with text — a memorial, names, and a count.",
        },
        {
            "id":      "commanders_log",
            "title":   "Commander's Siege Log",
            "source":  "a military log on a collapsed desk near the entrance",
            "trigger": "search",
            "content": (
                "Day 1: 'Creatures from the rift. Not like the void-touched we were warned about. "
                "These are older. Larger. They do not speak but they wait. They are patient.'\n\n"
                "Day 4: 'We have lost nine. The creatures do not eat the dead. They leave them. "
                "I think it is a message.'\n\n"
                "Day 7: 'Veyne says hold. We hold.'\n\n"
                "Day 9: 'Something large moved in the rift tonight. A shape. "
                "It looked at us. I think it is the King. I think he is still in there. "
                "I think he knows what he did.'\n\n"
                "Day 11: 'End of log. Veyne is gone. We will hold one more day.'\n\n"
                "No Day 12 entry."
            ),
            "hint": "A desk has collapsed against the wall, papers scattered. One bound log has stayed mostly intact.",
        },
    ],

    "watchtower_peak": [
        {
            "id":      "observers_log",
            "title":   "The Observer's Log",
            "source":  "a logbook chained to the railing at the peak",
            "trigger": "examine",
            "content": (
                "Entries going back thirty years — weather, patrols, unusual sightings. "
                "The final entry:\n\n"
                "'Dark Moon night. Clear sky. Excellent visibility north.\n"
                "2nd hour: Light from the keep district — unusual colour, deep red.\n"
                "3rd hour: Ground tremor lasting approximately forty seconds. "
                "The stones of the tower cracked on the east face.\n"
                "4th hour: The light in the north is — '"
            ),
            "hint": "A logbook chained to the railing is open to its final entry, the last line incomplete.",
        },
        {
            "id":      "astronomers_chart",
            "title":   "The Dark Moon Chart",
            "source":  "a star chart pinned to the wall inside the watchtower room",
            "trigger": "search",
            "content": (
                "A detailed astronomical chart showing the 'Dark Moon' alignment — "
                "when Valdris passes through the shadow of a dead star. "
                "The chart notes:\n\n"
                "'Occurs once per century. The void membrane is at its thinnest during the "
                "three-hour window of full alignment. Ancient texts suggest the void "
                "is aware of this thinning and presses against it from the other side.\n\n"
                "NEXT ALIGNMENT: Third month, seventeenth day — this year.'\n\n"
                "The chart is dated 300 years ago. The predicted date matches the date "
                "carved on the burial arch. The astronomer knew exactly when it would happen. "
                "Someone knew and did not stop it."
            ),
            "hint": "A star chart pinned to the wall shows a celestial alignment circled in red, with a date written beneath it.",
        },
    ],

    "forgotten_camp": [
        {
            "id":      "letters_never_sent",
            "title":   "Letters Never Sent",
            "source":  "a bundle of sealed letters tied with rope, hanging from a tent peg",
            "trigger": "examine",
            "content": (
                "Seven letters, all addressed to people in other towns — towns that no longer "
                "exist or that survivors could never reach. "
                "One is unsealed:\n\n"
                "'Dear Father,\n"
                "I am alive. I am at the camp south of the bridge. There are thirty of us. "
                "We have food for two weeks.\n"
                "I have tried to leave the island. The water does not let us leave. "
                "There is something in it — or the island holds us, I am not sure which.\n"
                "We tried four boats. All four came back. The sailors say the sea changes "
                "direction when you go too far. Like it forgets where it was going.\n"
                "I do not know if you are alive. I am writing anyway.\n"
                "I will try to reach you somehow. Or I will die trying.\n— Elara'"
            ),
            "hint": "A bundle of letters hangs from a tent peg, tied carefully — someone meant to send them and never could.",
        },
        {
            "id":      "camp_rules",
            "title":   "The Camp Rules",
            "source":  "a piece of bark nailed to a post with rules scratched into it",
            "trigger": "search",
            "content": (
                "CAMP RULES — agreed by all:\n\n"
                "1. No fires after dark (they see the light)\n"
                "2. Water from the south stream only (the north water is changed)\n"
                "3. Do not approach the void bridge alone\n"
                "4. Do not speak of the King's name (it upsets people)\n"
                "5. Watch rotation: Elara, Cort, Brin, Deva, then repeat\n"
                "6. Anyone who shows void-touch signs (grey veining, cold hands, "
                "hearing the hum) must report it\n"
                "7. We leave together or not at all\n\n"
                "Rule 7 is crossed out. Below it, in different handwriting:\n"
                "'Some of us are still here.'"
            ),
            "hint": "A piece of bark is nailed to a post with handwritten rules — the last one is crossed out.",
        },
    ],

    "void_altar": [
        {
            "id":      "ancient_carvings",
            "title":   "The Old Carvings",
            "source":  "engravings on the altar base, partially covered by newer markings",
            "trigger": "examine",
            "content": (
                "The altar is older than the Shattering — much older. "
                "Beneath the cultists' recent symbols, older carvings are visible:\n\n"
                "'Do not call to what waits beyond the wall. "
                "It hears everything. It does not distinguish between invitation and accident.\n"
                "If you must approach the void, do not name yourself. "
                "Do not look into the rift directly. Do not make an offering. "
                "It will remember you. It will always remember you.'\n\n"
                "Someone — the Awakened — has partially chiseled these warnings away "
                "and carved their own text over them:\n"
                "'HE WAITS. WE CALL. HE WILL ANSWER.'"
            ),
            "hint": "The altar base has layered carvings — old words partially destroyed and overwritten with new ones.",
        },
        {
            "id":      "ritual_diagram",
            "title":   "The Ritual Diagram",
            "source":  "a burned schematic on the ground beside the altar",
            "trigger": "search",
            "content": (
                "A technical diagram, partially burned — the ritual Aldros used. "
                "It shows seven circles arranged around a central point, "
                "each labeled with a Shard placement. "
                "One circle is filled in: 'Anchor Shard — placed.' "
                "The other six are empty.\n\n"
                "A handwritten note in the margin, in the King's handwriting:\n"
                "'One Shard is sufficient to open the rift. "
                "Seven Shards would open it permanently — no closing from either side.'\n\n"
                "Below this, in different ink, much more recent:\n"
                "'We have found four. Three remain.'"
            ),
            "hint": "On the ground near the altar, a burned diagram is weighted down with a stone — geometric, deliberate.",
        },
    ],

    "shattered_spire": [
        {
            "id":      "final_prediction",
            "title":   "The Astronomer's Prediction",
            "source":  "a brass plate mounted to the spire wall, engraved with precision",
            "trigger": "examine",
            "content": (
                "PREDICTION OF CATASTROPHIC VOID CONTACT:\n"
                "Prepared by Royal Astronomer Cassiel, 300 years ago\n\n"
                "'Based on void membrane thinning cycles, void creature migration patterns, "
                "and the trajectory of void-touch spread through the northern ruins, "
                "I calculate that an uncontrolled void rift opening will occur within "
                "three years of this writing — sooner if accelerated by ritual contact.\n\n"
                "I presented this to the King. He thanked me for the information.\n\n"
                "I presented it to the Council. They thanked me for my service.\n\n"
                "I am nailing this plate to the wall of the Spire because I do not know "
                "what else to do. If you are reading this after the Shattering:\n"
                "I tried. I want that on the record. I tried.'\n\n"
                "The prediction was accurate to within eleven days."
            ),
            "hint": "A brass plate is mounted to the wall — a formal engraving, official in tone, with a date in the header.",
        },
        {
            "id":      "shard_map",
            "title":   "The Shard Scatter Map",
            "source":  "a torn map pinned to a broken telescope, hand-drawn",
            "trigger": "search",
            "content": (
                "A map of Valdris Island, roughly drawn. "
                "Seven X marks are scattered across it with short labels:\n\n"
                "'Based on the Shard's mass, the rift's force at detonation, "
                "and the prevailing winds that night — these are where the pieces landed.\n\n"
                "If anyone finds this: the Shards must be destroyed, not collected. "
                "Combining them does not close the rift. It opens it further. "
                "Anyone collecting them either does not know this or does not care.\n\n"
                "If the cult finds all seven before you do, do not try to fight them "
                "at the altar. Go to the Ritual Chamber. That is where they will go. "
                "That is where it ends.'"
            ),
            "hint": "A torn map is pinned to the largest telescope, hand-drawn with X marks and annotations.",
        },
    ],

    "underground_vault": [
        {
            "id":      "merchants_account",
            "title":   "The Merchant's Account",
            "source":  "a personal ledger wedged behind a collapsed shelf, dense with writing",
            "trigger": "search",
            "content": (
                "'I hid in the vault when the tremors started. Forty-three days.\n\n"
                "From the ventilation grate I watched the street. "
                "First: soldiers running north. Then: ash. Then: things in the ash "
                "that were not soldiers anymore.\n\n"
                "On the ninth day, a man walked through the street below. "
                "Not running. Walking. He was wearing the King's colors but they were burned. "
                "He looked up at the grate. I do not know if he saw me. "
                "His eyes were wrong — the wrong color. Everything wrong. "
                "He kept walking.\n\n"
                "I don't think that was the King. But I think it used to be.'"
            ),
            "hint": "Behind a collapsed shelf, a ledger is wedged — personal, dense writing, not accounts.",
        },
        {
            "id":      "hidden_inventory",
            "title":   "The Pre-Shattering Cache",
            "source":  "a wax-sealed inventory list inside a hidden compartment in the floor",
            "trigger": "examine",
            "content": (
                "A sealed inventory: gold, jewels, deeds, grain stores. "
                "The header reads:\n\n"
                "'Emergency reserve — in case of the worst outcome. "
                "For rebuilding. Not for speculation. Not for personal enrichment.\n"
                "If you are reading this after a disaster: take what you need. "
                "Leave what you do not. This belongs to whoever survives.'\n\n"
                "Dated seven months before the Shattering.\n\n"
                "Someone knew. Seven months before the end, someone "
                "believed it was coming and prepared for after. "
                "They never came back to collect it."
            ),
            "hint": "A section of the floor sounds hollow — something is hidden beneath a flagstone.",
        },
    ],

    "void_chasm_edge": [
        {
            "id":      "warning_stones",
            "title":   "The Boundary Markers",
            "source":  "a line of carved standing stones along the chasm edge",
            "trigger": "examine",
            "content": (
                "The stones are carved with a simple repeated message in the old script:\n\n"
                "'DO NOT APPROACH THE TEAR — placed here in the second year after Shattering, "
                "by the survivors' council of Saltmarsh, to mark the boundary of what is safe. "
                "Beyond this line, the void has touched the stone. The stone remembers it. "
                "The stone is not stone anymore.'\n\n"
                "The stones are cracked. Several have been knocked over. "
                "Fresh bootprints lead past them toward the chasm."
            ),
            "hint": "A line of standing stones runs parallel to the chasm, each carved with the same warning.",
        },
        {
            "id":      "void_etched_message",
            "title":   "What the Void Carved",
            "source":  "letters formed in the chasm wall itself — not carved by human hands",
            "trigger": "search",
            "content": (
                "The chasm wall is not smooth. It has been shaped — not by tools "
                "but by something pressing from inside, leaving impressions in the stone "
                "that resolve, when you step back far enough, into letters:\n\n"
                "'I REMEMBER YOU'\n\n"
                "Not a threat. Not a greeting. A statement of fact.\n\n"
                "Below it, in the same formless lettering:\n"
                "'I HAVE ALWAYS REMEMBERED YOU'\n\n"
                "Below that, barely visible:\n"
                "'I AM STILL HERE'"
            ),
            "hint": "The chasm wall isn't smooth — step back far enough and the irregularities form something that looks almost like letters.",
        },
    ],

    "saltmarsh_gate": [
        {
            "id":      "welcome_arch_names",
            "title":   "The Welcome Arch",
            "source":  "the gate arch itself, covered in carved names from centuries of travelers",
            "trigger": "examine",
            "content": (
                "The tradition on Valdris was to carve your name in the arch when you arrived, "
                "and carve a small symbol when you left safely. "
                "The arch is covered in thousands of names and symbols.\n\n"
                "The names and departure symbols stop abruptly at the same date — "
                "the date of the Shattering. After that: nothing for a long blank section.\n\n"
                "Then, much lower, recent carvings begin again. "
                "But they are not names. They are the broken-circle symbol "
                "of the Awakened cult. Dozens of them, added over the past few years.\n\n"
                "And one, in the old style — a single name, recently carved: 'Elara.'\n"
                "No departure symbol next to it."
            ),
            "hint": "The gate arch is covered in carvings — thousands of names and symbols, then a long gap, then something different.",
        },
    ],

    "dockside": [
        {
            "id":      "sailors_log",
            "title":   "The Sailor's Log",
            "source":  "a waterproof case washed against the dock pilings, still sealed",
            "trigger": "search",
            "content": (
                "'Attempt 1 — Three days after Shattering. Eight survivors, one fishing boat. "
                "Sailed east for six hours. The island was still visible. "
                "We kept sailing. Two hours later, the island was still the same size. "
                "We turned back.\n\n"
                "Attempt 2 — Two weeks later. Twelve survivors, the large trader. "
                "Sailed north for ten hours. The island remained equidistant. "
                "No other land in any direction. The compass spun.\n\n"
                "Attempt 3 — One month later. Just me and Cort. Small boat, no supplies. "
                "Sailed straight west and kept going. For three days.\n"
                "On the fourth day the boat was in the harbor again. "
                "We had not turned. We had not slept.\n"
                "The island kept us. Or the void does.\n"
                "I stopped trying after that.'"
            ),
            "hint": "A sealed waterproof case is wedged between the dock pilings, half buried in silt.",
        },
    ],

    "crumbling_watchtower": [
        {
            "id":      "scout_report",
            "title":   "A Scout's Early Report",
            "source":  "a military report in a dispatch pouch on the wall",
            "trigger": "examine",
            "content": (
                "Filed seven days before the Shattering:\n\n"
                "'Scout Report — Northern perimeter. "
                "Void creature sightings have increased to eleven in the past week. "
                "This is the highest weekly count on record. "
                "Requesting additional garrison at the bridge.\n\n"
                "Also noting: a group of approximately twenty individuals has been observed "
                "camping near the void altar. They have not responded to hails. "
                "They appear to be conducting rituals of some kind. "
                "Recommending investigation.'\n\n"
                "Stamped: RECEIVED. No follow-up action noted.\n\n"
                "The cult had been operating openly for at least a week before the Shattering. "
                "The garrison saw them. No one investigated."
            ),
            "hint": "A dispatch pouch is nailed to the wall, standard military issue, still sealed.",
        },
    ],

    "tavern_back_room": [
        {
            "id":      "smugglers_cache",
            "title":   "The Smuggler's Manifest",
            "source":  "a hidden manifest inside a loose floor panel",
            "trigger": "search",
            "content": (
                "'Shipment log — not for official eyes:\n\n"
                "Void crystal fragments — buyer: unnamed, paid in advance, "
                "triple the market rate. Fifteen shipments over two years.\n\n"
                "I asked what they wanted them for. The buyer said 'a collection.' "
                "I didn't push it. The money was good.\n\n"
                "Last shipment: two weeks before the Shattering. "
                "Unusually large order. The buyer sent six people to collect.\n\n"
                "I know what happened. I know what the crystals were for.\n"
                "The money is still in the floor. I cannot spend it.\n"
                "It sits there and it accuses me every day.'"
            ),
            "hint": "One of the floorboards sounds different when stepped on — hollow, deliberately loose.",
        },
    ],

    "healers_hut": [
        {
            "id":      "void_sickness_notes",
            "title":   "Medical Notes on Void-Touch",
            "source":  "a leather medical folio on the treatment shelf",
            "trigger": "examine",
            "content": (
                "Notes from the healer who preceded Sable, three generations back:\n\n"
                "'Void-touch presents in stages:\n"
                "Stage 1: Grey veining under the skin, cold to the touch. Patient feels nothing unusual.\n"
                "Stage 2: Hearing loss, replaced by a hum the patient describes as 'a voice that isn't speaking yet.'\n"
                "Stage 3: Dissociation — patient speaks of feeling 'pulled' in a direction. "
                "Refuses to leave the direction of the rift.\n"
                "Stage 4: Non-responsive. Patient moves toward the rift if unrestrained. "
                "Cannot be redirected.\n"
                "Stage 5: Contact. Patient enters the rift perimeter. Not recovered.\n\n"
                "I have treated forty-one cases. Forty-one have progressed to Stage 5.\n"
                "I have no cure. I have only postponement. I am sorry.'"
            ),
            "hint": "A leather folio on the treatment shelf is heavily annotated — medical notes, not standard texts.",
        },
    ],
}


def get_location_lore(location_key: str) -> list[dict]:
    """Returns all lore entries for a location."""
    return LOCATION_LORE.get(location_key, [])


def get_undiscovered_lore(location_key: str, player_lore: list[str]) -> list[dict]:
    """Returns lore entries the player hasn't found yet."""
    discovered = set(player_lore)
    return [e for e in get_location_lore(location_key) if e["id"] not in discovered]


def get_lore_prompt_block(location_key: str, player_lore: list[str]) -> str:
    """
    Returns a block to inject into the AI prompt describing what lore is
    discoverable here. Uses hints only — never reveals full content to the AI
    so it narrates organically rather than dumping text.
    """
    undiscovered = get_undiscovered_lore(location_key, player_lore)
    if not undiscovered:
        return ""

    lines = ["DISCOVERABLE LORE HERE (weave hints into narration naturally — do not recite content):"]
    for entry in undiscovered:
        lines.append(f"- [{entry['source']}]: {entry['hint']} (lore_id: {entry['id']})")
    return "\n".join(lines)


def get_lore_by_id(lore_id: str) -> dict | None:
    """Look up a lore entry by ID across all locations."""
    for entries in LOCATION_LORE.values():
        for entry in entries:
            if entry["id"] == lore_id:
                return entry
    return None
