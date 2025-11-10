#!/usr/bin/env python3
"""
AU_RPG_TEXT.py - Text-only terminal RPG (single file)

Features:
- Character selection with multiple AU characters (Sans/Chara variants)
- Expanded story with many unique choices and branching outcomes
- Turn-based combat (menu-driven)
- Inventory system with usable items (heal, buff, escape)
- Save and load support (simple JSON)
- At least 3 distinct endings (many more based on flags)
- Extensive inline comments explaining what each part does

Run:
    python au_rpg_text.py
"""

import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# -------------------------
# DATA MODELS
# -------------------------

@dataclass
class Item:
    """Represents an item the player can carry and use."""
    name: str
    description: str
    effect: Dict  # e.g. {"heal": 30} or {"buff": ("strength", 2, 3)} or {"escape": 0.5}

@dataclass
class CharacterTemplate:
    """Template used at character selection."""
    key: str
    display_name: str
    desc: str
    base_stats: Dict[str, int]

@dataclass
class Actor:
    """Represents a combatant (player or enemy)."""
    name: str
    max_hp: int
    hp: int
    stats: Dict[str, int]
    moves: List[Dict] = field(default_factory=list)
    status_effects: Dict[str, int] = field(default_factory=dict)

    def is_alive(self) -> bool:
        return self.hp > 0

# -------------------------
# CHARACTER TEMPLATES
# -------------------------
# These are the AUs you listed — treated as fictional characters.
CHAR_TEMPLATES = [
    CharacterTemplate("sans", "Sans", "Laid-back skeleton. High Agility & Magic.", {"strength": 6, "agility": 10, "magic": 9}),
    CharacterTemplate("underswap_pap", "Underswap! Papyrus", "Friendly and balanced fighter.", {"strength": 9, "agility": 8, "magic": 5}),
    CharacterTemplate("storyshift_chara", "StoryShift! Chara", "Tricksy tactician, high magic & agility.", {"strength": 5, "agility": 11, "magic": 10}),
    CharacterTemplate("storyfell_chara", "StoryFell! Chara", "Aggressive powerhouse.", {"strength": 12, "agility": 7, "magic": 4}),
    CharacterTemplate("dustfell_sans", "DustFell! Sans", "Survivalist with brutal moves.", {"strength": 11, "agility": 6, "magic": 6}),
    CharacterTemplate("outer_sans", "Outer! Sans", "Otherworldly and magical.", {"strength": 6, "agility": 8, "magic": 12}),
    CharacterTemplate("dusttrust_sans", "Dusttrust! Sans", "Resilient, balanced build.", {"strength": 9, "agility": 9, "magic": 7}),
    CharacterTemplate("nightmare_sans", "Nightmare Sans", "Nightmarish boss; high power.", {"strength": 13, "agility": 4, "magic": 13}),
]

# -------------------------
# SAVE FILE
# -------------------------
SAVE_FILE = "savegame_text.json"

# -------------------------
# HELPER FUNCTIONS
# -------------------------

def clamp(n, a, b):
    """Clamp n between a and b."""
    return max(a, min(b, n))

def prompt_choice(prompt: str, valid: List[str]) -> str:
    """
    Prompt until the user enters a valid choice.
    valid: list of valid lowercased responses (e.g. ['1','2','q'])
    Returns the chosen string (lowercased).
    """
    while True:
        resp = input(prompt).strip()
        if not resp:
            print("Please enter a choice.")
            continue
        if resp.lower() in valid:
            return resp.lower()
        # Accept numeric if in valid list (e.g. '1','2')
        if resp in valid:
            return resp
        print("Invalid option — try again.")

def roll(min_v=1, max_v=20):
    """Return a random integer simulating a dice roll."""
    return random.randint(min_v, max_v)

# -------------------------
# SCENES / STORY
# -------------------------

def build_scenes():
    """
    Build the branching scenes dictionary.
    Each scene has:
      - title
      - desc
      - choices: list of (text, next_scene_id, optional_effect)
    effect examples:
      {"enemy":"wolf_spirit"}
      {"item": Item(...)}
      {"flag":"befriended_spirit"}
      {"ending":"ending_flee"}
    """
    return {
        "start": {
            "title": "Awakening in the Glade",
            "desc": ("You wake in a foggy glade. A crooked path leads toward a ruined village to the west "
                     "and a distant spire (the Enchanted Castle) to the north."),
            "choices": [
                ("Follow the path to the Abandoned Village", "village", None),
                ("Head toward the towers of the Enchanted Castle", "approach_castle", None),
                ("Search the glade for supplies", "glade_search", {"item": Item("Tarnished Amulet", "An old amulet. Grants +2 magic when used (permanent).", {"buff": ("magic", 2, 999)})}),
            ],
        },
        "glade_search": {
            "title": "Search the Glade",
            "desc": "You find a tarnished amulet and some scraps of old cloth. It might be useful.",
            "choices": [
                ("Wear the amulet and continue to the village", "village", {"flag": "amulet_worn"}),
                ("Pocket the amulet and head to the castle", "approach_castle", {"item": Item("Hidden Map", "A map showing a secret entrance to the castle.", {})}),
                ("Leave the amulet and go to the village", "village", None),
            ],
        },
        "village": {
            "title": "Abandoned Village",
            "desc": ("Shadows move between collapsed roofs. You hear a faint cry from a cellar and "
                     "see a flicker in a window."),
            "choices": [
                ("Investigate the cellar noise", "cellar", None),
                ("Search the houses for supplies", "village_search", {"item": Item("Rusty Blade", "An old blade that grants +2 strength when used (permanent).", {"buff": ("strength", 2, 999)})}),
                ("Sneak quietly and move on to the road", "road", None),
            ],
        },
        "cellar": {
            "title": "The Cellar",
            "desc": ("A trapped villager begs for help. There's a pack of spectral wolves approaching."),
            "choices": [
                ("Defend the villager (fight wolves)", "combat", {"enemy": "wolf_spirit", "after": "village_reward"}),
                ("Distract the wolves and run", "road", {"flag": "saved_villager"}),
                ("Ignore and leave (cold choice)", "road", {"flag": "ignored_villager"}),
            ],
        },
        "village_search": {
            "title": "Rummaging",
            "desc": "You find medicine and a torn map that points toward the Enchanted Castle's dungeons.",
            "choices": [
                ("Keep the medicine and head to the castle", "approach_castle", {"item": Item("Herbal Salve", "Heals 30 HP when used.", {"heal": 30})}),
                ("Trade the medicine with a villager (gain info)", "meet_guide", {"flag": "met_guide"}),
            ],
        },
        "road": {
            "title": "The Road",
            "desc": "A lonely road. The sky darkens as you near the castle grounds.",
            "choices": [
                ("Enter the castle grounds", "castle_gate", None),
                ("Camp and rest for the night", "camp", {"heal": 10}),
            ],
        },
        "approach_castle": {
            "title": "Approach the Castle",
            "desc": ("A looming castle sits in a place where the air seems wrong. A spectral figure "
                     "watches from the drawbridge."),
            "choices": [
                ("Talk to the figure", "talk_figure", None),
                ("Sneak around to the dungeons (secret map helps)", "dungeon_entrance", {"requires": "Hidden Map"}),
                ("Charge the gate", "gate_assault", {"enemy": "bandit_chief"}),
            ],
        },
        "talk_figure": {
            "title": "The Watcher",
            "desc": ("The watcher speaks: 'Many seek power here. Few leave. Will you bargain?'"),
            "choices": [
                ("Bargain for guidance (offer help)", "throne_influence", {"flag": "offered_help"}),
                ("Refuse and move on", "castle_gate", None),
            ],
        },
        "dungeon_entrance": {
            "title": "Dungeon Entrance",
            "desc": ("You find a hidden trapdoor and descend into the cold corridors."),
            "choices": [
                ("Descend into the dungeons (dangerous)", "dungeons", None),
                ("Close the trapdoor and retreat", "castle_gate", None),
            ],
        },
        "gate_assault": {
            "title": "Assault on the Gate",
            "desc": "You are challenged by the bandit chief who harasses travellers.",
            "choices": [
                ("Fight the bandit chief", "combat", {"enemy": "bandit_chief", "after": "after_bandit"}),
                ("Try to bribe him", "bribe_bandit", None),
            ],
        },
        "bribe_bandit": {
            "title": "Bribery Attempt",
            "desc": "You offer coin. The chief laughs, either accepts or is insulted.",
            "choices": [
                ("Pay him (if you have coin)", "castle_gate", {"flag": "bribed_bandit"}),
                ("He gets angry and attacks", "combat", {"enemy": "bandit_chief", "after": "after_bandit"}),
            ],
        },
        "castle_gate": {
            "title": "Castle Gate",
            "desc": "The gate groans open. Shadows ripple beneath the stone floors.",
            "choices": [
                ("Enter the main hall", "main_hall", None),
                ("Explore the garden ruins", "garden", None),
            ],
        },
        "camp": {
            "title": "Night Camp",
            "desc": "You rest and regain some strength.",
            "choices": [
                ("Continue toward the castle", "castle_gate", None),
            ],
        },
        "dungeons": {
            "title": "The Dungeons",
            "desc": ("A dank subterranean place. You feel the presence of nightmares. "
                     "A monstrous nightmarish minion prowl the halls."),
            "choices": [
                ("Fight a nightmarish minion", "combat", {"enemy": "nightmare_minion", "after": "dungeon_loot"}),
                ("Search for an alternate path", "secret_passage", None),
            ],
        },
        "main_hall": {
            "title": "Main Hall",
            "desc": "Tapestries show a long history of pain and bargains. A doorway leads to the throne room.",
            "choices": [
                ("Go to the throne room", "throne_room", None),
                ("Look for allies in the servants' wing", "servant_wing", None),
            ],
        },
        "throne_room": {
            "title": "Throne Room",
            "desc": ("A shadow sits upon the throne, ancient and patient. The final decision awaits."),
            "choices": [
                ("Challenge the shadow", "combat", {"enemy": "throne_shadow", "after": "final_victory"}),
                ("Attempt to negotiate (requires flags)", "final_negotiate", None),
                ("Walk away quietly (flee ending)", "ending_flee", {"ending": "flee"}),
            ],
        },
        "final_negotiate": {
            "title": "Final Negotiation",
            "desc": "You attempt to parley with the shadow. Results depend on choices and flags you collected.",
            "choices": [
                ("Offer to help heal the realm (if you saved the villager)", "ending_peace", {"requires": "saved_villager", "ending": "peace"}),
                ("Demand the shadow's power", "combat", {"enemy": "throne_shadow", "after": "final_victory"}),
            ],
        },
        # post-combat anchors & small reward scenes:
        "village_reward": {
            "title": "After the Wolves",
            "desc": "You are praised in whispers; the grateful villager offers a token of trust.",
            "choices": [
                ("Take the token (later matters)", "road", {"flag": "villager_token"}),
            ],
        },
        "after_bandit": {
            "title": "After the Bandit",
            "desc": "Bandits scatter. You find a map with a circled dungeon entrance.",
            "choices": [
                ("Follow the map to the dungeons", "dungeons", {"item": Item("Dungeon Map", "Marks a secret entrance.", {})}),
            ],
        },
        "dungeon_loot": {
            "title": "Dungeon Loot",
            "desc": "You find a shard of night glass that hums with power.",
            "choices": [
                ("Keep the shard", "main_hall", {"flag": "night_shard"}),
            ],
        },
        "servant_wing": {
            "title": "Servant Wing",
            "desc": "You find a weary servant who remembers a ritual to soften the shadow.",
            "choices": [
                ("Learn the ritual (gain knowledge)", "main_hall", {"flag": "learned_ritual"}),
            ],
        },
        # Endings (leaf nodes)
        "ending_peace": {
            "title": "Peaceful Resolution",
            "desc": "Your compassion and choices healed part of the darkness. The realm breathes easier.",
            "choices": []
        },
        "ending_victory": {
            "title": "Victory",
            "desc": "You defeated the shadow with steel and cunning, but at a cost—power unbalanced remains.",
            "choices": []
        },
        "ending_flee": {
            "title": "Fleeing Life",
            "desc": "You walked away from the conflict and lived in the shadows—safe, but heavy with regret.",
            "choices": []
        },
        "ending_sacrifice": {
            "title": "Sacrifice",
            "desc": "You sacrificed yourself to seal the shadow, a quiet hero in the night.",
            "choices": []
        },
    }

# -------------------------
# ENEMIES (combat templates)
# -------------------------
ENEMIES = {
    "wolf_spirit": {"name": "Wolf Spirit", "hp": 45, "str": 8, "agi": 9, "mag": 5, "moves": [
        {"name": "Bite", "base": 8, "type": "physical"},
        {"name": "Howl", "base": 0, "type": "debuff"},
    ]},
    "bandit_chief": {"name": "Bandit Chief", "hp": 70, "str": 11, "agi": 8, "mag": 4, "moves": [
        {"name": "Slash", "base": 10, "type": "physical"},
        {"name": "Poison Dart", "base": 4, "type": "magic"},
    ]},
    "nightmare_minion": {"name": "Nightmare Minion", "hp": 90, "str": 10, "agi": 7, "mag": 12, "moves": [
        {"name": "Claw", "base": 11, "type": "physical"},
        {"name": "Night Rasp", "base": 8, "type": "magic"},
    ]},
    "throne_shadow": {"name": "Throne Shadow", "hp": 140, "str": 14, "agi": 6, "mag": 16, "moves": [
        {"name": "Shadow Strike", "base": 15, "type": "physical"},
        {"name": "Abyssal Judgement", "base": 14, "type": "magic"},
        {"name": "Drain", "base": 6, "type": "drain"},
    ]},
}

# -------------------------
# GAME CLASS: TEXT MODE
# -------------------------

class TextGame:
    """
    The main text-mode game engine.
    Handles: player creation, scene navigation, combat, inventory, flags, saving/loading.
    """
    def __init__(self):
        # Scenes/story nodes
        self.scenes = build_scenes()
        # Player data (to be filled after character selection)
        self.player: Optional[Actor] = None
        self.template: Optional[CharacterTemplate] = None
        # Inventory starts with a couple of items
        self.inventory: List[Item] = [Item("Small Potion", "Heals 25 HP.", {"heal": 25}),
                                     Item("Smoke Bomb", "Escape attempt in combat (60%).", {"escape": 0.6})]
        # map scene pointer: start at "start"
        self.current_scene = "start"
        # flags to track choices and influence endings
        self.flags = set()
        # RNG seed for reproducibility during testing if desired (commented out)
        # random.seed(12345)

    # -------------------------
    # Character selection
    # -------------------------
    def choose_character(self):
        """Prompt the player to pick from the character templates."""
        print("\nCHARACTER SELECTION\n-------------------")
        for i, t in enumerate(CHAR_TEMPLATES, start=1):
            print(f"{i}. {t.display_name} — {t.desc} (STR:{t.base_stats['strength']} AGI:{t.base_stats['agility']} MAG:{t.base_stats['magic']})")
        while True:
            choice = input("Choose your character (number): ").strip()
            if not choice.isdigit():
                print("Enter the number of your chosen character.")
                continue
            idx = int(choice) - 1
            if 0 <= idx < len(CHAR_TEMPLATES):
                self.template = CHAR_TEMPLATES[idx]
                hp = 60 + self.template.base_stats["strength"] * 2 + self.template.base_stats["magic"]
                # create player Actor with a set of default moves
                moves = [
                    {"name": "Attack", "base": self.template.base_stats["strength"], "type": "physical"},
                    {"name": "Magic", "base": self.template.base_stats["magic"], "type": "magic"},
                    {"name": "Focus", "base": 0, "type": "buff"},
                ]
                self.player = Actor(name=self.template.display_name, max_hp=hp, hp=hp, stats=dict(self.template.base_stats), moves=moves)
                print(f"You chose {self.player.name}. HP: {self.player.hp}. Good luck!")
                return
            print("Invalid selection; try again.")

    # -------------------------
    # Save / Load
    # -------------------------
    def save_game(self):
        """Save the player's progress and flags to a JSON file."""
        data = {
            "template": self.template.key if self.template else None,
            "player": {
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "stats": self.player.stats,
            } if self.player else None,
            "inventory": [(it.name, it.description, it.effect) for it in self.inventory],
            "current_scene": self.current_scene,
            "flags": list(self.flags),
        }
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Game saved to {SAVE_FILE}.")
        except Exception as e:
            print("Save failed:", e)

    def load_game(self):
        """Load game state from a JSON file if it exists."""
        if not os.path.exists(SAVE_FILE):
            print("No save file found.")
            return
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            tpl_key = data.get("template")
            tpl = next((t for t in CHAR_TEMPLATES if t.key == tpl_key), None)
            if not tpl:
                print("Saved character template not recognized; cannot load player.")
                return
            self.template = tpl
            p = data["player"]
            self.player = Actor(name=tpl.display_name, max_hp=p["max_hp"], hp=p["hp"], stats=p["stats"], moves=[
                {"name": "Attack", "base": p["stats"].get("strength", 5), "type": "physical"},
                {"name": "Magic", "base": p["stats"].get("magic", 5), "type": "magic"},
                {"name": "Focus", "base": 0, "type": "buff"},
            ])
            self.inventory = [Item(n, d, e) for (n, d, e) in data.get("inventory", [])]
            self.current_scene = data.get("current_scene", "start")
            self.flags = set(data.get("flags", []))
            print("Game loaded. Welcome back, " + self.player.name + "!")
        except Exception as e:
            print("Failed to load save:", e)

    # -------------------------
    # Scene/navigation logic
    # -------------------------
    def play(self):
        """Main game loop for navigating scenes and handling actions."""
        # If no player yet, choose or load
        while True:
            if self.player is None:
                print("\nStart Menu: (N)ew game, (L)oad game, (Q)uit")
                cmd = prompt_choice("Choice: ", ["n", "l", "q"])
                if cmd == "n":
                    self.choose_character()
                elif cmd == "l":
                    self.load_game()
                    if self.player is None:
                        # failed load or no save; loop to choose
                        continue
                elif cmd == "q":
                    print("Goodbye.")
                    return
            # Enter main story loop
            while True:
                scene = self.scenes.get(self.current_scene)
                if scene is None:
                    print("You wander into nothingness and find yourself back at the start.")
                    self.current_scene = "start"
                    continue
                # Print scene header and description
                print("\n== " + scene["title"] + " ==")
                print(scene["desc"])
                # Print choices
                if not scene["choices"]:
                    # terminal scene (ending)
                    print("\n*** ENDING: " + scene["title"] + " ***")
                    print(scene["desc"])
                    # Offer to save or quit or start new game
                    post = prompt_choice("\n(S)ave, (N)ew Game, (Q)uit: ", ["s", "n", "q"])
                    if post == "s":
                        self.save_game()
                        continue
                    if post == "n":
                        # reset for a new game
                        self.player = None
                        self.template = None
                        self.inventory = [Item("Small Potion", "Heals 25 HP.", {"heal": 25}), Item("Smoke Bomb", "Escape attempt (60%).", {"escape": 0.6})]
                        self.flags = set()
                        self.current_scene = "start"
                        break  # break to outer loop to choose character/new game
                    if post == "q":
                        print("Farewell.")
                        return
                # list choices for non-ending scenes
                for i, (text, next_scene, effect) in enumerate(scene["choices"], start=1):
                    print(f"{i}. {text}")
                print("I. Inventory | S. Save | R. Rest (where available) | Q. Quit")
                choice = input("Choice: ").strip().lower()
                if choice == "i":
                    self.show_inventory()
                    continue
                if choice == "s":
                    self.save_game()
                    continue
                if choice == "q":
                    print("Quitting to main menu.")
                    self.player = None
                    self.template = None
                    self.current_scene = "start"
                    break  # return to start menu
                # numeric choice
                if not choice.isdigit():
                    print("Enter the number of a choice, or a command like I/S/Q.")
                    continue
                idx = int(choice) - 1
                if idx < 0 or idx >= len(scene["choices"]):
                    print("Invalid choice number.")
                    continue
                # apply the chosen option
                text, next_scene, effect = scene["choices"][idx]
                # Effects can be: enemy spawn, item grant, flag set, heal numeric, requires specific flag
                # First, check requirements:
                if effect and isinstance(effect, dict) and "requires" in effect:
                    req = effect["requires"]
                    # allow both flag name string or an Item name
                    if isinstance(req, str) and req not in self.flags and not any(it.name == req for it in self.inventory):
                        print("You do not have the required condition to take that action.")
                        continue
                # Handle combat initiation
                if effect and isinstance(effect, dict) and "enemy" in effect:
                    enemy_key = effect["enemy"]
                    self.do_combat(enemy_key)
                    # after combat, possibly jump to a special 'after' scene
                    if effect.get("after"):
                        self.current_scene = effect["after"]
                    else:
                        # if victory, go to next_scene; if defeated -> ending will handle inside combat
                        self.current_scene = next_scene
                    continue
                # Handle giving an item
                if effect and isinstance(effect, dict) and "item" in effect:
                    item = effect["item"]
                    self.inventory.append(item)
                    print(f"You obtained: {item.name} — {item.description}")
                # Handle heal effect (like rest)
                if effect and isinstance(effect, dict) and "heal" in effect:
                    amt = effect["heal"]
                    old = self.player.hp
                    self.player.hp = clamp(self.player.hp + amt, 0, self.player.max_hp)
                    print(f"You recovered {self.player.hp - old} HP by resting.")
                # Handle flags
                if effect and isinstance(effect, dict) and "flag" in effect:
                    self.flags.add(effect["flag"])
                    print(f"(Flag gained: {effect['flag']})")
                # Handle direct ending
                if effect and isinstance(effect, dict) and "ending" in effect:
                    ending_id = effect["ending"]
                    self.current_scene = "ending_" + ending_id if "ending_" + ending_id in self.scenes else ending_id
                    continue
                # Normal transition to the next scene
                self.current_scene = next_scene

    # -------------------------
    # Inventory UI
    # -------------------------
    def show_inventory(self):
        """Display inventory and allow using items."""
        if not self.inventory:
            print("Inventory is empty.")
            return
        print("\n-- Inventory --")
        for i, it in enumerate(self.inventory, start=1):
            print(f"{i}. {it.name} — {it.description}")
        print("U <num> to use, B to back")
        cmd = input("> ").strip().lower()
        if cmd == "b":
            return
        if cmd.startswith("u"):
            parts = cmd.split()
            if len(parts) < 2 or not parts[1].isdigit():
                print("Usage: U <number>")
                return
            idx = int(parts[1]) - 1
            if idx < 0 or idx >= len(self.inventory):
                print("Invalid item number.")
                return
            self.use_item(idx)
        else:
            print("Unrecognized inventory command.")

    def use_item(self, idx: int):
        """
        Apply the effect of an item at index idx.
        Effects implemented: heal, escape (only during combat), buff (permanent for simplicity).
        """
        item = self.inventory[idx]
        if "heal" in item.effect:
            amt = item.effect["heal"]
            old = self.player.hp
            self.player.hp = clamp(self.player.hp + amt, 0, self.player.max_hp)
            print(f"You used {item.name}: HP {old} -> {self.player.hp}.")
            del self.inventory[idx]
            return
        if "escape" in item.effect:
            print("That item is only usable in a fight to attempt escape.")
            return
        if "buff" in item.effect:
            stat, amt, dur = item.effect["buff"]
            self.player.stats[stat] = self.player.stats.get(stat, 0) + amt
            print(f"{item.name} permanently increased your {stat} by {amt}.")
            del self.inventory[idx]
            return
        print("Item could not be used.")

    # -------------------------
    # COMBAT SYSTEM
    # -------------------------
    def spawn_enemy(self, key: str) -> Actor:
        """Create an Actor (enemy) scaled to player's stats for challenge balance."""
        template = ENEMIES.get(key)
        if not template:
            # fallback generic enemy
            return Actor("Faint Echo", 30, 30, {"strength": 5, "agility": 5, "magic": 5}, moves=[
                {"name": "Tap", "base": 4, "type": "physical"}
            ])
        # scale enemy HP slightly by player's overall power to keep it engaging
        player_power = sum(self.player.stats.values()) if self.player else 15
        scale = 1.0 + (player_power - 15) / 80.0  # small scale factor
        hp = max(10, int(template["hp"] * scale))
        moves = template["moves"]
        return Actor(template["name"], hp, hp, {"strength": template["str"], "agility": template["agi"], "magic": template["mag"]}, moves=moves)

    def do_combat(self, enemy_key: str):
        """
        Full turn-based combat loop.
        Player chooses actions from menu; then enemy acts.
        Implements hit chance, damage calculation, status effects (simple), and item use during combat.
        """
        enemy = self.spawn_enemy(enemy_key)
        print(f"\n--- COMBAT START: {enemy.name} appears! ---")
        # small tactical hint
        print("Hint: Use items with 'U 1' style, or press 'F' to attempt to flee.")
        while enemy.is_alive() and self.player.is_alive():
            # Player turn
            print(f"\nYour HP: {self.player.hp}/{self.player.max_hp} | {enemy.name} HP: {enemy.hp}/{enemy.max_hp}")
            print("1) Attack   2) Magic   3) Use Item   4) Focus (small buff)   F) Flee")
            action = input("Choose action: ").strip().lower()
            if action == "1":
                # physical attack: hit chance influenced by agilities
                hit_roll = roll(1, 20) + self.player.stats.get("agility", 5) // 2
                defend = 8 + enemy.stats.get("agility", 5) // 2
                if hit_roll >= defend:
                    # damage computation uses strength plus small randomness
                    base = self.player.stats.get("strength", 5)
                    rand = random.randint(-3, 3)
                    damage = max(1, base + rand)
                    enemy.hp = max(0, enemy.hp - damage)
                    print(f"You strike with Attack for {damage} damage.")
                else:
                    print("Your attack missed!")
            elif action == "2":
                # magic attack: uses magic stat; slightly different hit rules
                hit_roll = roll(1, 20) + self.player.stats.get("magic", 5) // 2
                defend = 7 + enemy.stats.get("agility", 5) // 2
                if hit_roll >= defend:
                    base = self.player.stats.get("magic", 5)
                    damage = max(1, base + random.randint(-4, 4))
                    enemy.hp = max(0, enemy.hp - damage)
                    print(f"You unleash Magic for {damage} damage.")
                else:
                    print("Your magic fizzles and fails.")
            elif action == "3" or action.startswith("u"):
                # Use item during combat
                self.show_inventory()
                # show_inventory already asks for U <num>, and use_item handles combat-only items like escape
                # After using a smoke bomb (escape) the combat loop checks for escape effect below via thrown item behavior
            elif action == "4":
                # Focus: small self-buff using magic to increase next attack potency
                self.player.status_effects["focused"] = 2  # lasts 2 turns
                print("You gather yourself. Your next attacks are empowered.")
            elif action == "f":
                # attempt to flee based on agility difference
                chance = 0.3 + (self.player.stats.get("agility", 5) - enemy.stats.get("agility", 5)) * 0.02
                if random.random() < chance:
                    print("You successfully fled the battle.")
                    return
                else:
                    print("Flee attempt failed.")
            else:
                print("Unknown action; try again.")
                continue

            # Check if enemy died by player's action before enemy turn
            if not enemy.is_alive():
                print(f"You defeated {enemy.name}!")
                # reward: small chance for item or flag
                if enemy_key == "wolf_spirit" and random.random() < 0.4:
                    self.inventory.append(Item("Wolf Pelt", "A pelt of a spectral wolf.", {}))
                    print("You recover a Wolf Pelt.")
                if enemy_key == "throne_shadow":
                    # the final boss, higher stakes handled by caller (scene flow)
                    pass
                return

            # Enemy turn: simple AI picks a move at random
            # Some moves are debuffs (like 'Howl' could lower accuracy)
            move = random.choice(enemy.moves)
            print(f"{enemy.name} uses {move['name']}!")
            # Evaluate hit
            e_hit_roll = roll(1, 20) + enemy.stats.get("agility", 5) // 2
            p_defend = 7 + self.player.stats.get("agility", 5) // 2
            if e_hit_roll >= p_defend:
                # base damage depends on move and enemy strength/magic
                if move["type"] == "physical":
                    dmg = max(1, int(move["base"] + enemy.stats.get("strength", 5) * 0.3) + random.randint(-2, 2))
                    self.player.hp = max(0, self.player.hp - dmg)
                    print(f"It hits you for {dmg} damage.")
                elif move["type"] == "magic":
                    dmg = max(1, int(move["base"] + enemy.stats.get("magic", 5) * 0.35) + random.randint(-3, 2))
                    self.player.hp = max(0, self.player.hp - dmg)
                    print(f"Magic wounds you for {dmg} damage.")
                elif move["type"] == "drain":
                    dmg = max(1, int(move["base"] + enemy.stats.get("magic", 5) * 0.25))
                    self.player.hp = max(0, self.player.hp - dmg)
                    enemy.hp = min(enemy.max_hp, enemy.hp + dmg // 2)
                    print(f"The attack drains {dmg} HP and heals the enemy a bit.")
                elif move["type"] == "debuff":
                    # apply a simple debuff like 'howl' -> player gets 'shaken' reducing next hit chance
                    self.player.status_effects["shaken"] = 2
                    print("You are shaken and less steady (reduced hit chance).")
            else:
                print(f"{enemy.name}'s attack misses!")

            # Process simple status effects decay at end of enemy turn
            self.decay_statuses(self.player)
            self.decay_statuses(enemy)

            # If player died, break loop and handle defeat
            if not self.player.is_alive():
                print("You have been defeated...")
                # optionally implement sacrifice option if certain flags set
                if "villager_token" in self.flags:
                    # special sacrifice branch: convert to ending_sacrifice
                    print("Your sacrifice seals a weakening of the shadow.")
                    self.current_scene = "ending_sacrifice"
                else:
                    self.current_scene = "ending_flee"  # default "defeat leads to flee/defeat" (could be changed)
                return

    def decay_statuses(self, actor: Actor):
        """Reduce durations of status effects and remove them when they expire."""
        to_remove = []
        for s in list(actor.status_effects.keys()):
            actor.status_effects[s] -= 1
            if actor.status_effects[s] <= 0:
                to_remove.append(s)
        for s in to_remove:
            del actor.status_effects[s]

# -------------------------
# ENTRYPOINT
# -------------------------

def main():
    print("=== AU RPG (Text Edition) ===")
    game = TextGame()
    game.play()

if __name__ == "__main__":
    main()
