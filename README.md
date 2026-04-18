# Yahtzii Pro

Yahtzii Pro is a PyQt6 desktop Yahtzee-style scorecard with an optional animated digital roller. It supports 1 to 8 players, includes Yahtzii bonus and Joker handling, tracks game and turn timers, and can be played with either physical dice or a fully in-app roller. The current build includes a 10-theme picker in Registration that carries into the roller and scorecard. fileciteturn6file3turn6file18

---

## Features

- 1 to 8 players
- Registration screen with add/remove player controls
- Optional digital roller mode
- Theme picker with 10 themes: Classic, Forest, Ocean, Sunset, Storm, Neon, Lava, Lemon, Arctic, Cyber
- Automatic multiplayer roll-off with tie re-rolls
- Scorecard with upper section, lower section, Yahtzii bonus, and grand total calculation
- Digital roller score restriction and category highlighting after a confirmed roll
- Joker priority handling after bonus Yahtziis
- Dual timers for total game time and active turn time
- High score tracking saved to JSON
- Play-again flow with same-order, roll-order, new-game, and quit options fileciteturn6file3turn6file7turn6file16turn6file17

---

## Requirements

- Python 3.10+
- PyQt6
- PyQt6-Qt6
- PyQt6-sip

Install dependencies with:

```bash
pip install PyQt6 PyQt6-Qt6 PyQt6-sip
```

The app uses `QSvgWidget` and `QSvgRenderer` from PyQt6 for die rendering. The current script keeps fallback die faces inline, so no external art assets are required for the base app. fileciteturn6file3

---

## Running

```bash
python yahtzii.py
```

---

## Files

```text
yahtzii.py
README.md
images/                 # optional custom SVG die faces
yahtzee_highscores.json # created automatically after completed games
```

If `images/1.svg` through `images/6.svg` are present, the roller will try to use them. Otherwise it falls back to built-in SVG path data. High scores are written to `yahtzee_highscores.json`. fileciteturn6file15

---

## Game Flow

1. **Registration**
   - Enter player names.
   - Enable or disable Digital Roller.
   - Pick a theme.

2. **Roll-Off**
   - In multiplayer games, you can roll for order or keep registration order.
   - Tied players are re-rolled automatically.

3. **Scorecard Game**
   - Players take turns filling categories.
   - In digital mode, the roller opens automatically each turn.
   - At game end, choose Same Order, Roll for Order, New Game / Change Players, or Quit. fileciteturn6file14turn6file7

---

## Registration

The registration dialog supports up to 8 players and includes:

- Add Player
- Remove Player
- Digital Roller checkbox
- Theme picker

Current theme list:

- Classic
- Forest
- Ocean
- Sunset
- Storm
- Neon
- Lava
- Lemon
- Arctic
- Cyber fileciteturn5file0

---

## Scoring Rules

### Upper Section

Rows **Ones** through **Sixes** store the count of matching dice. The app multiplies the selected count by the face value when calculating the score. Reaching **63 or more** in the upper total awards the **35-point bonus**. fileciteturn6file1

### Lower Section

- **3 of a Kind**: total of all 5 dice
- **4 of a Kind**: total of all 5 dice
- **Full House**: 25 points
- **Small Straight**: 30 points
- **Large Straight**: 40 points
- **Yahtzii**: 50 points
- **Chance**: total of all 5 dice
- **Yahtzii Bonus**: +100 per additional Yahtzii when the Yahtzii box already contains 50 fileciteturn6file1turn6file17

### Scoring Zero

Any open category can be scored as 0. In digital roller mode, non-qualifying categories are restricted to 0 after dice confirmation. fileciteturn6file17

---

## Digital Roller

In digital mode:

- The roller opens at the start of each turn.
- Press **ROLL** to animate the dice.
- Click dice to hold them between rolls.
- You may confirm early with **✔ Done — Use These Dice**.
- After confirmation, the scorecard unlocks and valid categories are restricted to the exact score outcomes for that roll.
- If you hide the roller, the scorecard can reopen it with **🎲 Open Roller** without losing roll state. fileciteturn6file0turn6file8turn6file17

The roller includes animated dice widgets, hold glow, a power bar, bounce/flip animation, and a short roll history list. fileciteturn6file3turn6file8

---

## Joker Rules

After a valid bonus Yahtzii, the app enters Joker handling.

- If the matching upper box is open, that row must be used first.
- If the matching upper box is already claimed, open lower rows become the legal target set.
- The turn banner and cell highlighting indicate the currently legal choices. fileciteturn6file17

---

## Score Corrections

A claimed score can be temporarily unclaimed by setting it back to `—`, then replaced before the actual turn score is finalized. This correction flow does not by itself consume the turn. fileciteturn6file17

---

## Timers and Status

The scorecard window includes:

- a total game timer
- a turn timer
- a leader summary
- upper-section progress messaging
- last-scored category and streak/status text

The turn timer changes color as time increases. fileciteturn6file14turn6file17

---

## Toolbar and Dialogs

Main scorecard actions include:

- High Scores
- Reset
- Rules
- Open Roller (digital mode)

Dialogs in the app include:

- `PlayerSetupDialog`
- `RollOffDialog`
- `RulesDialog`
- `GameOverDialog` fileciteturn6file1turn6file7

---

## High Scores

Completed games can be written to `yahtzee_highscores.json` with player name, score, and date. The file is maintained as a top-10 list. fileciteturn6file7

---

## Notes

- This README reflects the currently uploaded `yahtzii.py`.
- The update changed the in-app Rules dialog copy and refreshed the README to match the current feature set.
- No gameplay logic was changed as part of this documentation update. fileciteturn5file0turn6file1
