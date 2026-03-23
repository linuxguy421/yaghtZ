# Yahtzee Pro

A full-featured desktop Yahtzee scorecard built with Python and PyQt6. Supports 1–8 players, enforces official rules (including Joker rules and Yahtzee bonuses), and optionally replaces physical dice with an animated digital roller.

---

## Requirements

```
Python 3.10+
PyQt6
```

```bash
pip install PyQt6 PyQt6-Qt6 PyQt6-sip
```

---

## Running

```bash
python yahtzee.py
```

---

## Project Structure

```
yahtzee-project/
│
├── yahtzee.py                  # Main application (scorecard + roller)
│
├── images/                     # Optional custom die artwork
│   ├── 1.svg
│   ├── 2.svg
│   ├── 3.svg
│   ├── 4.svg
│   ├── 5.svg
│   └── 6.svg
│
└── yahtzee_highscores.json     # Auto-generated on first game completion
```

The `images/` folder is optional. If absent, the app falls back to built-in inline SVG dice. `yahtzee_highscores.json` is created automatically in the working directory when the first game ends.

---

## Setup & Registration

On launch you are presented with the registration screen. Enter 1–8 player names. Players will take turns in the order listed unless you use the roll-off to randomise order.

### Digital Roller

Tick **🎲 Use Digital Roller** to play a fully digital game. Each player rolls animated dice in a separate window instead of physical dice. The scorecard locks during rolling and unlocks once the player confirms their roll.

Leave it unchecked to use the app as a **scorecard only** — roll your own physical dice and enter scores manually.

---

## Determining Turn Order

After registration the Roll-Off screen appears.

- **🎲 Roll for All Players** — animates a virtual dice roll for each player. Highest total goes first. Ties are automatically re-rolled between tied players only.
- **Start Scoring** — skips the roll and uses registration order directly.

---

## Playing a Turn

### Physical Dice Mode

Roll your own dice (up to three rolls per turn), then select a score from the dropdown in your column for the category you want to claim. Selecting any value other than **—** on an unclaimed box claims it and advances to the next player.

### Digital Roller Mode

1. The roller window opens automatically at the start of each turn, showing the current player's name.
2. Press **ROLL** (hold the button to charge the power bar for extra drama).
3. Click any dice to **hold** them, then press **ROLL** again — up to 3 rolls total.
4. You may confirm early after any roll; you are not forced to use all 3.
5. Click **✔ Done — Use These Dice** to lock in the roll.
6. The scorecard unlocks and highlights which categories score with that roll. Choose a category to end your turn.

If you accidentally close the roller window, click **🎲 Open Roller** on the scorecard toolbar to bring it back. Your roll state is preserved.

---

## Scoring

### Upper Section (Ones – Sixes)

Score only the dice matching that face value. The dropdown shows the count of matching dice; the app multiplies by face value automatically (e.g. three 4s → select 3 → scores 12).

Score 63 or more in the upper section to earn a **+35 bonus**.

### Lower Section

| Category | Score |
|---|---|
| 3 of a Kind | Total of all 5 dice |
| 4 of a Kind | Total of all 5 dice |
| Full House | Fixed 25 pts |
| Small Straight | Fixed 30 pts |
| Large Straight | Fixed 40 pts |
| Yahtzee | Fixed 50 pts |
| Chance | Total of all 5 dice |

Fixed-score categories only offer their fixed value or 0 — no manual entry needed.

### Scoring a Zero

You may score a **0** in any open category at any time — useful when a roll doesn't fit anywhere better. In digital roller mode, categories your roll cannot score are highlighted in **red** with only 0 available. You can still select them to burn the category.

---

## Digital Roller — Scorecard Highlighting

After confirming a roll, the scorecard colour-codes every unclaimed category for the active player:

| Colour | Meaning |
|---|---|
| Blue (normal) | Valid scoring option — select your score |
| Red | Roll cannot score here — only 0 is offered |

Dropdowns are also restricted to only the valid options for your roll:

- **Upper section** — shows only the exact count of matching dice (e.g. three 6s → dropdown offers 3 only)
- **3/4 of a Kind, Chance** — shows only the actual dice total when the roll qualifies
- **Fixed-score categories** — shows only the fixed value when the roll qualifies; 0 otherwise

---

## Yahtzee Bonus & Joker Rules

If you roll a second (or further) Yahtzee **and** your Yahtzee box already shows 50, click the **+** button in the Yahtzee Bonus row to add 100 points. Each click counts one bonus Yahtzee.

A bonus Yahtzee activates **Joker Rules**. When the 🃏 banner appears, follow this priority:

1. **Matching Upper box open?** You must score there (e.g. five 4s → score in Fours).
2. **Matching Upper box full?** Score in any open Lower box at full value.
3. **All Lower boxes full?** Enter a 0 in any open Upper box.

The scorecard highlights valid Joker choices and dims invalid ones automatically.

---

## Correcting a Score

Before scoring your turn, you may fix a previously claimed box:

1. Reset the box back to **—** — an amber warning appears.
2. Fill that box (or any other) with the correct value — a green confirmation appears.
3. Score your actual turn by claiming any **unclaimed** box — the turn ends normally.

Corrections are free edits and do not consume your turn.

---

## Themes

The digital roller includes five colour themes: **Classic**, **Forest**, **Ocean**, **Sunset**, and **Storm**. Switching themes in the roller window automatically repaints the scorecard to match.

---

## Game Over & Play Again

When all players have filled every category the winner is announced. Four options are presented:

| Option | Behaviour |
|---|---|
| ▶ Same Order | Instant rematch with the same turn order |
| 🎲 Roll for Order | Go to the roll-off screen to re-randomise order |
| 📋 New Game / Change Players | Return to the registration screen |
| ✖ Quit | Exit the application |

---

## High Scores

The winner's name and score are saved automatically at the end of every game in `yahtzee_highscores.json` (top 10 all-time). Click **High Scores** on the scorecard toolbar to view the leaderboard at any time.
