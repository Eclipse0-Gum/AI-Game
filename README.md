# AU_RPG_TEXT — Terminal-Based Undertale AU RPG (Python)

**AU_RPG_TEXT** is a text-only, turn-based RPG played entirely in the terminal.  
You choose from several Undertale AU character variants and explore a branching narrative with multiple endings, tactical combat, and an inventory system.  

This game runs in a single `.py` file and saves progress to JSON, making it portable and easy to modify.

---

## 🎮 Features

- **Character Selection**  
  Choose from several AU characters (Sans / Chara variants) each with unique stat profiles.

- **Branching Story Path**  
  Navigate scenes, make narrative decisions, unlock flags, and influence which ending you get.

- **Turn-Based Combat System**  
  Strategy matters — attacks use stats, agility influences hit chance, and magic damage behaves differently.

- **Inventory & Items**  
  Use healing items, buffs, or escape tools. Some items provide **permanent stat upgrades**.

- **Save & Load Support**  
  Restart from where you left off — progress is stored in `savegame_text.json`.

- **Multiple Endings**  
  Your choices change your outcome (peace, victory, sacrifice, flee, and more).

---

## 🛠 Requirements

- **Python 3.7+**
- No external libraries required (only built-in Python modules are used)

---

## ▶️ How to Run

Open a terminal in the directory containing the file and run:

```bash
python3 au_rpg_text.py
