#!/usr/bin/env python3

import sys
import random
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                             QScrollArea, QHeaderView, QFileDialog, QComboBox, QTextEdit,
                             QStatusBar)
from PyQt6.QtCore import Qt, QTimer, QEventLoop, QByteArray
from PyQt6.QtGui import QColor, QFont, QBrush
from PyQt6.QtSvgWidgets import QSvgWidget

# --- Theme Configuration ---
CLR_BACKGROUND = "#121212"
CLR_TABLE = "#1E1E1E"
CLR_UNCLAIMED = "#2A2A2A"          
CLR_ACTIVE_UNCLAIMED = "#3D3D3D"   
CLR_TOTAL_BG = "#000000"
CLR_ACCENT = "#03DAC6"
CLR_CLAIMED_TEXT = "#BB86FC"
CLR_ACTIVE_TURN = "#FFD700"
CLR_DISABLED = "#151515"
CLR_VALID = "#2E7D32" 
CLR_INVALID = "#C62828"
CLR_ACCENT_HOVER = "#00B3A4"
CLR_PURPLE_HOVER = "#9B59D0"

def accent_btn_style():
    return (f"QPushButton {{ background-color: {CLR_ACCENT}; color: black; border-radius: 4px; padding: 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {CLR_ACCENT_HOVER}; }}")

def purple_btn_style():
    return (f"QPushButton {{ background-color: {CLR_CLAIMED_TEXT}; color: black; border-radius: 4px; padding: 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {CLR_PURPLE_HOVER}; }}")

DARK_STYLESHEET = f"""
    QMainWindow, QDialog, QWidget {{ background-color: {CLR_BACKGROUND}; color: #E0E0E0; }}
    QTableWidget {{ background-color: {CLR_TABLE}; color: #E0E0E0; gridline-color: #333333; border: 1px solid #333333; }}
    QHeaderView::section {{ background-color: #252525; color: #BB86FC; padding: 5px; border: 1px solid #333333; font-weight: bold; }}
    QComboBox, QLineEdit {{ background-color: {CLR_UNCLAIMED}; color: white; border: 1px solid #3D3D3D; border-radius: 3px; padding: 2px; }}
    QPushButton {{ background-color: #333333; color: white; border-radius: 4px; padding: 10px; font-weight: bold; }}
    QPushButton:hover {{ background-color: #444444; }}
"""

UPPER_SECTION = [0, 1, 2, 3, 4, 5]
LOWER_SECTION_PRIMARY = [9, 10, 11, 12, 13, 16] # Categories that can be Jokers
FIXED_SCORE_ROWS = {11: 25, 12: 30, 13: 40, 14: 50}
CALCULATED_ROWS = [6, 7, 8, 17, 18]
PRIMARY_CATEGORIES = [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 16]

ROW_LABELS = (["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"] + 
              ["Sum", "Bonus (35)", "Total Upper"] + 
              ["3 of a Kind", "4 of a Kind", "Full House", "Small Straight", 
               "Large Straight", "Yahtzee", "Yahtzee Bonus (Count)", "Chance"] + 
              ["Total Lower", "GRAND TOTAL"])

class RulesDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Official Yahtzee Rules")
        self.resize(660, 750)
        layout = QVBoxLayout(self)
        rules_text = QTextEdit()
        rules_text.setReadOnly(True)
        rules_text.setHtml("""
            <h2 style='color: #03DAC6;'>Yahtzee Pro — How to Use This App</h2>

            <h3 style='color: #BB86FC;'>Object of the Game</h3>
            <p>Score the highest total across all 13 categories. The player with the highest Grand Total wins.</p>

            <h3 style='color: #BB86FC;'>Setting Up — Registration</h3>
            <p>Enter each player's name on the Registration screen. Up to 8 players are supported.</p>
            <p>This app is a <b>scorecard only</b> — you roll your physical dice yourself. The app tracks scores, enforces turn order, and calculates totals automatically.</p>
            <p><b>Tip:</b> If you prefer to determine turn order manually (e.g. by house rule or physical roll), enter players in the desired turn order and click <b>Start Scoring</b> on the Roll-Off screen without rolling.</p>

            <h3 style='color: #BB86FC;'>Determining Turn Order — Roll-Off Screen</h3>
            <p>The Roll-Off screen offers two options:</p>
            <ul>
                <li><b>🎲 Roll for All Players</b> — the app rolls 5 virtual dice for each player and animates the reveal one player at a time. Highest total goes first. Ties trigger an automatic re-roll between tied players only.</li>
                <li><b>Start Scoring</b> — skip the roll entirely and use the registration order as the turn order.</li>
            </ul>

            <h3 style='color: #BB86FC;'>Playing a Turn</h3>
            <p>Roll your physical dice (up to three rolls per turn, re-rolling any dice you choose). Then select your score from the dropdown in your column for the category you want to claim.</p>
            <ul>
                <li>Selecting any value other than <b>—</b> on an <b>unclaimed</b> box claims it and advances to the next player.</li>
                <li>You must claim exactly one unclaimed box per turn. You may enter <b>0</b> in any open box if your roll doesn't fit anywhere useful.</li>
            </ul>

            <h3 style='color: #BB86FC;'>Correcting a Score</h3>
            <p>Before scoring your turn, you may correct any previously claimed box:</p>
            <ol>
                <li>Reset the box back to <b>—</b> — an amber warning will appear reminding you a correction is in progress.</li>
                <li>Fill that box (or any other claimed box) with the correct value — a green confirmation will appear.</li>
                <li>Now score your actual turn by claiming any <b>unclaimed</b> box — the turn then ends normally.</li>
            </ol>
            <p>Corrections are free edits and do not consume your turn. The turn only ends when you score an unclaimed box.</p>

            <h3 style='color: #BB86FC;'>Upper Section</h3>
            <p>Score only the dice matching that category's face value. The dropdown shows how many of that die you rolled (0–5); the app multiplies by the face value automatically.</p>
            <ul>
                <li><b>Ones</b> through <b>Sixes</b> — select the count of matching dice (e.g. three 4s → select 3, scores 12)</li>
            </ul>
            <p><b>Bonus:</b> If your Upper Section subtotal reaches <b>63 or more</b>, you automatically receive a <b>+35 point bonus</b>. The running subtotal and bonus are calculated live.</p>

            <h3 style='color: #BB86FC;'>Lower Section</h3>
            <ul>
                <li><b>3 of a Kind</b> — at least three dice the same; enter the total of all 5 dice (5–30)</li>
                <li><b>4 of a Kind</b> — at least four dice the same; enter the total of all 5 dice (5–30)</li>
                <li><b>Full House</b> — three of one number and two of another; scores a fixed <b>25 points</b></li>
                <li><b>Small Straight</b> — any four sequential numbers; scores a fixed <b>30 points</b></li>
                <li><b>Large Straight</b> — five sequential numbers (1–5 or 2–6); scores a fixed <b>40 points</b></li>
                <li><b>Yahtzee</b> — five of a kind; scores a fixed <b>50 points</b></li>
                <li><b>Chance</b> — any roll; enter the total of all 5 dice (5–30)</li>
            </ul>
            <p>Fixed-score categories (Full House, Straights, Yahtzee) only offer their fixed value or 0 — no manual entry needed.</p>

            <h3 style='color: #BB86FC;'>Yahtzee Bonus</h3>
            <p>If you roll a second (or further) Yahtzee in the same game <b>and</b> your Yahtzee box is already scored as <b>50</b>, click the <b>+</b> button in your Yahtzee Bonus row to add 100 points. Each click counts one bonus Yahtzee.</p>
            <p>The Joker Rules below apply whenever a bonus Yahtzee is scored.</p>

            <hr style='border-color: #333;'/>
            <h3 style='color: #BB86FC;'>🃏 Joker Rules</h3>
            <p>A bonus Yahtzee acts as a Joker. When the <b>🃏 Joker Rules Active</b> banner appears, follow this priority in order:</p>
            <ol>
                <li><b>Matching Upper box open?</b> You <i>must</i> score there (e.g. five 4s → score in Fours).</li>
                <li><b>Matching Upper box full?</b> Score in any open Lower box using its full value:<br/>
                    Full House = 25 pts &nbsp;|&nbsp; Small Straight = 30 pts &nbsp;|&nbsp; Large Straight = 40 pts<br/>
                    3 of a Kind / 4 of a Kind / Chance = total of all 5 dice</li>
                <li><b>All Lower boxes full?</b> Enter a <b>0</b> in any open Upper box.</li>
            </ol>
            <p>The scorecard highlights valid choices and dims invalid ones during a Joker turn. Hover over any cell for a reminder of which step applies.</p>

            <hr style='border-color: #333;'/>
            <h3 style='color: #BB86FC;'>Play Again Options</h3>
            <p>At the end of a game the winner is announced and you are given three choices:</p>
            <ul>
                <li><b>▶ Same Order</b> — start a new game immediately with the identical turn order, no dialogs.</li>
                <li><b>🎲 Roll for Order</b> — go straight to the Roll-Off screen (players pre-filled) to re-determine order.</li>
                <li><b>✖ Quit</b> — exit the application.</li>
            </ul>

            <h3 style='color: #BB86FC;'>High Scores</h3>
            <p>The winner's score is saved automatically at the end of each game. The <b>High Scores</b> button shows the all-time top 10 winners stored in <i>yahtzee_highscores.json</i> in the same folder as the app.</p>
        """)
        layout.addWidget(rules_text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

class PlayerSetupDialog(QDialog):
    def __init__(self, prefill=None):
        super().__init__()
        self.setWindowTitle("Yahtzee Registration")
        self.setFixedSize(400, 500)
        self.player_inputs = []
        layout = QVBoxLayout(self)
        header = QLabel("Player Registration")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        hint = QLabel("💡 If rolling manually, enter players in turn order.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #888888; font-size: 11px; padding-bottom: 4px;")
        layout.addWidget(hint)
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.input_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        if prefill:
            for name in prefill:
                self.add_player_slot(name)
        else:
            self.add_player_slot()
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add Player")
        add_btn.clicked.connect(self.add_player_slot)
        rem_btn = QPushButton("- Remove Player")
        rem_btn.clicked.connect(self.remove_player_slot)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(rem_btn)
        layout.addLayout(btn_layout)
        self.next_btn = QPushButton("Next: Determine Order")
        self.next_btn.setStyleSheet(accent_btn_style())
        self.next_btn.clicked.connect(self.accept)
        layout.addWidget(self.next_btn)

    def add_player_slot(self, name=""):
        if len(self.player_inputs) < 8:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            inp = QLineEdit()
            inp.setPlaceholderText(f"Player {len(self.player_inputs) + 1}")
            if name:
                inp.setText(name)
            row_layout.addWidget(inp)
            self.input_layout.addWidget(row_widget)
            self.player_inputs.append((row_widget, inp))

    def remove_player_slot(self):
        if len(self.player_inputs) > 1:
            row_widget, _ = self.player_inputs.pop()
            row_widget.deleteLater()

def _load_die_svg(face: int, color: str) -> bytes:
    """Load images/{face}.svg and recolor the fill to `color`."""
    path = os.path.join("images", f"{face}.svg")
    try:
        with open(path, "r", encoding="utf-8") as f:
            svg = f.read()
    except FileNotFoundError:
        svg = f'<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="{color}"/></svg>'
    svg = svg.replace('fill="#000000"', f'fill="{color}"')
    svg = svg.replace("fill='#000000'", f"fill='{color}'")
    return svg.encode("utf-8")

class RollOffDialog(QDialog):
    def __init__(self, names):
        super().__init__()
        self.setWindowTitle("Roll-Off for Order")
        self.setMinimumWidth(620)

        # --- State (unchanged logic) ---
        self.names          = names
        self.player_scores  = {name: [] for name in names}
        self.to_roll        = list(names)
        self.sorted_names   = list(names)
        self.animation_counter = 0
        self._reveal_queue  = []
        self._final_rolls   = {}
        self._order_score   = {}   # name -> definitive score used for final sort

        # --- Layout ---
        outer = QVBoxLayout(self)
        outer.setSpacing(12)
        outer.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🎲 Roll-Off for Order")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {CLR_ACCENT}; padding-bottom: 4px;")
        outer.addWidget(title)

        self.info_lbl = QLabel("Roll to determine play order — highest total goes first.")
        self.info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_lbl.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        outer.addWidget(self.info_lbl)

        # --- Player cards ---
        self.cards       = {}   # name -> card QWidget
        self.dice_labels = {}   # name -> list of 5 QLabels
        self.score_labels= {}   # name -> score QLabel

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        card_container = QWidget()
        self.card_layout = QVBoxLayout(card_container)
        self.card_layout.setSpacing(8)
        scroll.setWidget(card_container)
        outer.addWidget(scroll)

        for name in names:
            self._build_card(name)

        # --- Buttons ---
        self.btn_roll = QPushButton("🎲 Roll for All Players")
        self.btn_roll.setStyleSheet(accent_btn_style())
        self.btn_roll.clicked.connect(self.start_animation)
        outer.addWidget(self.btn_roll)

        self.btn_start = QPushButton("Start Scoring")
        self.btn_start.setStyleSheet(accent_btn_style())
        self.btn_start.clicked.connect(self.accept)
        outer.addWidget(self.btn_start)

        # --- Timers ---
        self.shake_timer  = QTimer(); self.shake_timer.timeout.connect(self._shake_tick)
        self.reveal_timer = QTimer(); self.reveal_timer.timeout.connect(self._reveal_next)

        self.adjustSize()

    def _build_card(self, name):
        card = QWidget()
        card.setStyleSheet(
            f"background-color: #1E1E1E; border: 1px solid #333333;"
            f"border-radius: 8px; padding: 6px;"
        )
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(14)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_lbl.setFixedWidth(120)
        row.addWidget(name_lbl)

        dice_row = QHBoxLayout()
        dice_row.setSpacing(0)
        dice_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        dice_widgets = []
        for i in range(5):
            dice_row.addStretch(1)
            d = QSvgWidget()
            d.setFixedSize(44, 44)
            d.load(QByteArray(_load_die_svg(1, "#2A2A2A")))  # hidden placeholder
            dice_row.addWidget(d)
            dice_widgets.append(d)
        dice_row.addStretch(1)
        row.addLayout(dice_row)

        row.addStretch()

        score_lbl = QLabel("—")
        score_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        score_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        score_lbl.setStyleSheet("color: #666666; min-width: 40px;")
        row.addWidget(score_lbl)

        self.card_layout.addWidget(card)
        self.cards[name]        = card
        self.dice_labels[name]  = dice_widgets   # now QSvgWidgets
        self.score_labels[name] = score_lbl

    def _set_card_state(self, name, state):
        """state: 'idle' | 'rolling' | 'done' | 'tie' | 'winner'"""
        styles = {
            "idle":    ("border: 1px solid #333333;",           "#AAAAAA", "#555555"),
            "rolling": (f"border: 2px solid {CLR_ACCENT};",     "white",   CLR_ACCENT),
            "done":    ("border: 1px solid #444444;",           "#CCCCCC", CLR_CLAIMED_TEXT),
            "tie":     ("border: 2px solid #FFD700;",           "#FFD700", "#FFD700"),
            "winner":  (f"border: 2px solid {CLR_ACCENT};",     CLR_ACCENT, CLR_ACCENT),
        }
        border, name_color, score_color = styles.get(state, styles["idle"])
        self.cards[name].setStyleSheet(
            f"background-color: #1E1E1E; {border} border-radius: 8px; padding: 6px;"
        )
        # update name label color
        self.cards[name].findChild(QLabel).setStyleSheet(f"color: {name_color};")
        self.score_labels[name].setStyleSheet(f"color: {score_color}; min-width: 36px;")

    # ------------------------------------------------------------------ #
    #  Animation: shake all rolling players simultaneously                 #
    # ------------------------------------------------------------------ #
    def start_animation(self):
        self.btn_roll.setEnabled(False)
        self.animation_counter = 0
        for name in self.to_roll:
            self._set_card_state(name, "rolling")
            self.score_labels[name].setText("—")
        self.shake_timer.start(60)

    def _shake_tick(self):
        self.animation_counter += 1
        for name in self.to_roll:
            vals = [random.randint(1, 6) for _ in range(5)]
            for widget, v in zip(self.dice_labels[name], vals):
                widget.load(QByteArray(_load_die_svg(v, CLR_ACCENT)))
        if self.animation_counter >= 18:
            self.shake_timer.stop()
            self._compute_final_rolls()

    # ------------------------------------------------------------------ #
    #  Staggered reveal: lock in one player at a time                      #
    # ------------------------------------------------------------------ #
    def _compute_final_rolls(self):
        self._final_rolls = {}
        for name in self.to_roll:
            dice = [random.randint(1, 6) for _ in range(5)]
            self._final_rolls[name] = (dice, sum(dice))
        # reveal in the order they were listed (drama!)
        self._reveal_queue = list(self.to_roll)
        self.reveal_timer.start(420)

    def _reveal_next(self):
        if not self._reveal_queue:
            self.reveal_timer.stop()
            self.finalize_roll()
            return
        name = self._reveal_queue.pop(0)
        dice, total = self._final_rolls[name]
        for widget, v in zip(self.dice_labels[name], dice):
            widget.load(QByteArray(_load_die_svg(v, "#FFFFFF")))
        self.score_labels[name].setText(str(total))
        self._set_card_state(name, "done")

    # ------------------------------------------------------------------ #
    #  Finalize (same logic as before)                                     #
    # ------------------------------------------------------------------ #
    def finalize_roll(self):
        for name in self.to_roll:
            _, roll = self._final_rolls[name]
            self.player_scores[name].append(roll)
            self._order_score[name] = roll

        # Find ALL score groups among players who just rolled
        last_scores = {n: self.player_scores[n][-1] for n in self.to_roll}

        # Group players by score
        from collections import defaultdict
        score_groups = defaultdict(list)
        for n, s in last_scores.items():
            score_groups[s].append(n)

        # Any group with more than one player needs a re-roll
        self.to_roll = []
        for score, group in score_groups.items():
            if len(group) > 1:
                self.to_roll.extend(group)

        if not self.to_roll:
            # No ties — sort all players by definitive order score
            self.sorted_names = sorted(
                self.names,
                key=lambda n: self._order_score.get(n, 0),
                reverse=True
            )
            for name in self.sorted_names:
                self.card_layout.removeWidget(self.cards[name])
                self.card_layout.addWidget(self.cards[name])
            for name in self.names:
                self._set_card_state(name, "winner" if name == self.sorted_names[0] else "done")
            self.info_lbl.setText(f"🏆 {self.sorted_names[0]} goes first!")
            self.info_lbl.setStyleSheet(f"color: {CLR_ACCENT}; font-size: 12px; font-weight: bold;")
            self.btn_start.setStyleSheet(accent_btn_style())
        else:
            for name in self.to_roll:
                self._set_card_state(name, "tie")
            for name in self.names:
                if name not in self.to_roll:
                    self._set_card_state(name, "done")
            self.info_lbl.setText(f"⚠️  Tie! {', '.join(self.to_roll)} must re-roll.")
            self.info_lbl.setStyleSheet("color: #FFD700; font-size: 11px;")
            self.btn_roll.setText(f"🎲 Resolve Tie ({len(self.to_roll)} players)")
            self.btn_roll.setEnabled(True)

class GameOverDialog(QDialog):
    SAME_ORDER = 1
    ROLL_ORDER = 2
    QUIT       = 0

    PLACE_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

    def __init__(self, scores, parent=None):
        """scores: list of (name, score) sorted descending."""
        super().__init__(parent)
        self.setWindowTitle("Game Over!")
        self.setMinimumWidth(380)
        self.result_choice = self.QUIT
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        winner_name, winner_score = scores[0]
        msg = QLabel(f"🏆  {winner_name} wins with {winner_score} pts!")
        msg.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding-bottom: 4px;")
        layout.addWidget(msg)

        # --- Leaderboard ---
        for place, (name, score) in enumerate(scores, start=1):
            row_widget = QWidget()
            row_widget.setStyleSheet(
                f"background-color: {'#2A2200' if place == 1 else '#1E1E1E'};"
                f"border: 1px solid {'#FFD700' if place == 1 else '#333333'};"
                f"border-radius: 6px;"
            )
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(12, 6, 12, 6)

            medal = self.PLACE_MEDALS.get(place, f"#{place}")
            place_lbl = QLabel(medal)
            place_lbl.setFont(QFont("Arial", 13))
            place_lbl.setFixedWidth(32)
            row.addWidget(place_lbl)

            name_lbl = QLabel(name)
            name_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            name_lbl.setStyleSheet(f"color: {'#FFD700' if place == 1 else '#CCCCCC'};")
            row.addWidget(name_lbl)

            row.addStretch()

            score_lbl = QLabel(f"{score} pts")
            score_lbl.setFont(QFont("Arial", 11))
            score_lbl.setStyleSheet(f"color: {'#FFD700' if place == 1 else '#AAAAAA'};")
            row.addWidget(score_lbl)

            layout.addWidget(row_widget)

        # --- Buttons ---
        layout.addSpacing(4)
        sub = QLabel("Play again?")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        layout.addWidget(sub)

        btn_same = QPushButton("▶  Same Order")
        btn_same.setStyleSheet(accent_btn_style())
        btn_same.clicked.connect(lambda: self._pick(self.SAME_ORDER))
        layout.addWidget(btn_same)

        btn_roll = QPushButton("🎲  Roll for Order")
        btn_roll.setStyleSheet(purple_btn_style())
        btn_roll.clicked.connect(lambda: self._pick(self.ROLL_ORDER))
        layout.addWidget(btn_roll)

        btn_quit = QPushButton("✖  Quit")
        btn_quit.clicked.connect(lambda: self._pick(self.QUIT))
        layout.addWidget(btn_quit)

        self.adjustSize()

    def _pick(self, choice):
        self.result_choice = choice
        self.accept()

class YahtzeeScorecard(QMainWindow):
    def __init__(self, players):
        super().__init__()
        self.players, self.current_turn_index, self.play_again_requested, self._is_updating = players, 0, False, False
        self.joker_active = False
        self._correction_pending = False
        self._last_unclaimed_name = ""
        self._correction_replaced_msg = ""
        
        self.setWindowTitle("Yahtzee! Pro Scorecard")
        self.resize(1100, 900)
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        
        self.turn_label = QLabel("")
        self.turn_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.turn_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding: 10px;")
        layout.addWidget(self.turn_label)
        
        self.table = QTableWidget(len(ROW_LABELS), len(players))
        self.table.setVerticalHeaderLabels(ROW_LABELS)
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.setup_board()
        layout.addWidget(self.table)
        
        btns = QHBoxLayout()
        high_score_btn, reset, rules = QPushButton("High Scores"), QPushButton("Reset"), QPushButton("Rules")
        high_score_btn.clicked.connect(self.show_high_scores) 
        reset.clicked.connect(self.reset) 
        rules.clicked.connect(self.show_rules)
        btns.addWidget(high_score_btn); btns.addWidget(reset); btns.addWidget(rules)
        layout.addLayout(btns)

        # --- Status Bar (two rows, evenly spaced) ---
        sb_widget = QStatusBar()
        sb_widget.setSizeGripEnabled(False)
        sb_container = QWidget()
        sb_outer = QVBoxLayout(sb_container)
        sb_outer.setContentsMargins(8, 3, 8, 3)
        sb_outer.setSpacing(1)

        self._sb_row1 = QLabel()
        self._sb_row2 = QLabel()
        self._sb_row1.setTextFormat(Qt.TextFormat.RichText)
        self._sb_row2.setTextFormat(Qt.TextFormat.RichText)
        self._sb_row1.setStyleSheet(f"background-color: {CLR_TABLE}; font-size: 11px;")
        self._sb_row2.setStyleSheet(f"background-color: {CLR_TABLE}; font-size: 11px;")

        sb_outer.addWidget(self._sb_row1)
        sb_outer.addWidget(self._sb_row2)

        sb_widget.addWidget(sb_container, 1)
        sb_widget.setStyleSheet(
            f"QStatusBar {{ background-color: {CLR_TABLE}; border-top: 1px solid #333333; }}"
            f"QStatusBar::item {{ border: none; }}"
        )
        self.setStatusBar(sb_widget)

        # Internal data cache for status bar
        self._sb_data = {
            'leader': '', 'scores': '', 'last': '',
            'upper': '', 'upper_color': '#AAAAAA',
            'best': '', 'streak': '', 'alltime': '',
        }
        self._load_alltime_high()

        # Streak tracking state
        self._streak_player = None
        self._streak_count  = 0

        self.update_turn_ui()

    def closeEvent(self, event):
        # If the local event loop is running, tell it to exit
        if hasattr(self, 'loop') and self.loop.isRunning():
            self.loop.quit()
        event.accept()

    def show_rules(self):
        RulesDialog().exec()

    def setup_board(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = QTableWidgetItem("-")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, "unclaimed")
                
                if r in CALCULATED_ROWS:
                    item.setText("0"); item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(QColor(CLR_TOTAL_BG)); item.setForeground(QBrush(QColor(CLR_ACCENT)))
                elif r in UPPER_SECTION:
                    self.add_dropdown(r, c, ["-", "0", "1", "2", "3", "4", "5"])
                elif r == 15:
                    self.setup_yahtzee_bonus_cell(r, c)
                    continue 
                elif r in FIXED_SCORE_ROWS:
                    self.add_dropdown(r, c, ["-", str(FIXED_SCORE_ROWS[r]), "0"])
                elif r in [9, 10, 16]: 
                    self.add_dropdown(r, c, ["-", "0"] + [str(i) for i in range(5, 31)])
                else:
                    item.setBackground(QColor(CLR_UNCLAIMED))
                
                self.table.setItem(r, c, item)
        self.table.blockSignals(False)

    def setup_yahtzee_bonus_cell(self, r, c):
        container = QWidget()
        layout = QHBoxLayout(container); layout.setContentsMargins(2, 2, 2, 2)
        lbl = QLabel("0"); btn = QPushButton("+")
        btn.setFixedSize(25, 25); btn.clicked.connect(lambda checked, col=c: self.increment_yahtzee_bonus(col))
        layout.addWidget(lbl); layout.addWidget(btn)
        self.table.setCellWidget(r, c, container)
        item = QTableWidgetItem("0"); item.setData(Qt.ItemDataRole.UserRole, "bonus_row")
        self.table.setItem(r, c, item)

    def add_dropdown(self, r, c, options):
        combo = QComboBox()
        combo.addItems(options)
        combo.setProperty("row", r); combo.setProperty("col", c)
        combo.currentIndexChanged.connect(self.handle_dropdown)
        self.table.setCellWidget(r, c, combo)

    def _update_upper_dropdowns(self, c):
        """Swap upper section dropdown options based on joker state for the active column."""
        is_active = (c == self.current_turn_index)
        for r in UPPER_SECTION:
            combo = self.table.cellWidget(r, c)
            if not combo or not isinstance(combo, QComboBox): continue
            if self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "claimed": continue
            self._is_updating = True
            current = combo.currentText()
            combo.clear()
            if is_active and self.joker_active:
                combo.addItems(["-", "5", "0"])
            else:
                combo.addItems(["-", "0", "1", "2", "3", "4", "5"])
            # restore selection if still valid, else reset to "-"
            idx = combo.findText(current)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            self._is_updating = False

    def _update_streak(self, c, score):
        if score > 0:
            if getattr(self, '_streak_player', None) == self.players[c]:
                self._streak_count += 1
            else:
                self._streak_player = self.players[c]
                self._streak_count  = 1
        else:
            if getattr(self, '_streak_player', None) == self.players[c]:
                self._streak_player = None
                self._streak_count  = 0

    def handle_dropdown(self, index):
        if self._is_updating: return
        combo = self.sender()
        r, c = combo.property("row"), combo.property("col")

        self._is_updating = True
        item = self.table.item(r, c)
        status = item.data(Qt.ItemDataRole.UserRole)

        # ── Reset to "-" — free correction, no turn impact ────────────
        if combo.currentText() == "-":
            if status == "claimed":
                self._last_unclaimed_name = ROW_LABELS[r]
                item.setData(Qt.ItemDataRole.UserRole, "unclaimed")
                item.setText("-")
                self._correction_pending = True
                self.recalc(c)
                self.update_turn_ui()
            self._is_updating = False
            return

        old_val = item.text()  # capture before overwriting
        score = int(combo.currentText()) * (r + 1) if r in UPPER_SECTION else int(combo.currentText())
        item.setText(str(score))
        item.setData(Qt.ItemDataRole.UserRole, "claimed")

        if status == "unclaimed" and self._correction_pending:
            # ── Filling the reset box (replacement) — still their turn ─
            self._correction_pending = False
            self._correction_replaced_msg = (
                f"✔  {self._last_unclaimed_name} replaced by {ROW_LABELS[r]} — now score your current turn"
            )
            self.recalc(c)
            self.update_turn_ui()

        elif status == "unclaimed":
            # ── Normal turn score — end the turn ──────────────────────
            self._correction_replaced_msg = ""
            self._last_score_msg = f"Last score: {self.players[c]} → {ROW_LABELS[r]}  {score} pts"
            self._update_streak(c, score)
            self.recalc(c)
            self.advance_to_next_player()

        else:
            # ── Editing an already-claimed box — free edit, show alert, no turn impact
            self._correction_replaced_msg = (
                f"✔  {ROW_LABELS[r]} changed from {old_val} to {score} pts — now score your current turn"
            )
            self.recalc(c)
            self.update_turn_ui()

        self._is_updating = False

    def increment_yahtzee_bonus(self, c):
        y_score = self.table.item(14, c).text()
        if y_score != "50":
            QMessageBox.warning(self, "Rule Violation", "Yahtzee Bonus requires a 50 in the Yahtzee box!")
            return

        item = self.table.item(15, c)
        val = int(item.text()) + 1
        item.setText(str(val))
        self.table.cellWidget(15, c).findChild(QLabel).setText(str(val))
        
        self._last_score_msg = f"Last score: {self.players[c]} → Yahtzee Bonus  +100 pts"
        self.joker_active = True
        self.recalc(c)
        self.update_turn_ui()

    def advance_to_next_player(self):
        self.joker_active = False
        self._correction_pending = False
        self._last_unclaimed_name = ""
        self._correction_replaced_msg = ""
        total = len(self.players)
        for _ in range(total):
            self.current_turn_index = (self.current_turn_index + 1) % total
            if self.player_has_turns_left(self.current_turn_index):
                self.update_turn_ui()
                return
        self.check_game_over()

    def player_has_turns_left(self, c):
        return any(self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "unclaimed" for r in PRIMARY_CATEGORIES)

    def _load_alltime_high(self):
        """Read the top score from yahtzee_highscores.json and cache it."""
        filename = "yahtzee_highscores.json"
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    data = json.load(f)
                if data:
                    top = data[0]
                    self._sb_data['alltime'] = f"🏅 All-time: {top['name']} {top['score']} pts ({top['date']})"
                    return
        except Exception:
            pass
        self._sb_data['alltime'] = "🏅 All-time: —"

    def _render_status_bar(self):
        """Re-render both rows as evenly-spaced HTML tables."""
        d = self._sb_data

        def cell3(text, color, align="left", bold=False):
            weight = "font-weight:bold;" if bold else ""
            return (f"<td width='33%' style='color:{color};{weight}"
                    f"text-align:{align};white-space:nowrap;padding:0 4px;'>{text}</td>")

        def cell4(text, color, align="left", bold=False):
            weight = "font-weight:bold;" if bold else ""
            return (f"<td width='25%' style='color:{color};{weight}"
                    f"text-align:{align};white-space:nowrap;padding:0 4px;'>{text}</td>")

        row1 = (
            "<table width='100%' cellspacing='0' cellpadding='0'><tr>"
            + cell3(d['leader'],  CLR_ACTIVE_TURN,  "left",   bold=True)
            + cell3(d['scores'],  CLR_ACCENT,        "center")
            + cell3(d['last'],    CLR_CLAIMED_TEXT,  "right")
            + "</tr></table>"
        )
        row2 = (
            "<table width='100%' cellspacing='0' cellpadding='0'><tr>"
            + cell4(d['upper'],   d['upper_color'],  "left")
            + cell4(d['streak'],  "#FF8C00",         "center")
            + cell4(d['best'],    "#BB86FC",         "center")
            + cell4(d['alltime'], "#AAAAAA",         "right")
            + "</tr></table>"
        )
        self._sb_row1.setText(row1)
        self._sb_row2.setText(row2)

    def update_status_bar(self):
        if not hasattr(self, '_sb_data'): return

        totals = [int(self.table.item(18, c).text()) for c in range(len(self.players))]
        curr = self.current_turn_index
        d = self._sb_data

        # Row 1 — Leader
        best_c = totals.index(max(totals))
        d['leader'] = f"🏆 {self.players[best_c]} leading ({totals[best_c]} pts)"

        # Row 1 — Score Snapshot
        d['scores'] = "  ".join(f"{self.players[c]}: {totals[c]}" for c in range(len(self.players)))

        # Row 1 — Last Score
        d['last'] = getattr(self, '_last_score_msg', "")

        # Row 2 — Upper Bonus Progress (active player)
        u_sum = sum(int(self.table.item(r, curr).text()) for r in range(6) if self.table.item(r, curr).text().isdigit())
        if u_sum >= 63:
            d['upper'] = f"Upper: {self.players[curr]} {u_sum}/63 ✓ Bonus earned!"
            d['upper_color'] = CLR_ACCENT
        else:
            d['upper'] = f"Upper: {self.players[curr]} {u_sum}/63 — {63 - u_sum} needed for bonus"
            d['upper_color'] = '#AAAAAA'

        # Row 2 — Highest Single Score This Game
        best_score, best_who, best_cat = 0, "", ""
        for c in range(len(self.players)):
            for r in PRIMARY_CATEGORIES:
                item = self.table.item(r, c)
                if item and item.data(Qt.ItemDataRole.UserRole) == "claimed":
                    val = int(item.text()) if item.text().lstrip('-').isdigit() else 0
                    if val > best_score:
                        best_score, best_who, best_cat = val, self.players[c], ROW_LABELS[r]
        d['best'] = f"🎯 Best: {best_who} → {best_cat} ({best_score} pts)" if best_who else "🎯 Best: —"

        # Row 2 — Scoring Streak (falls back to closest competitor)
        streak_p = getattr(self, '_streak_player', None)
        streak_n = getattr(self, '_streak_count', 0)
        if streak_p and streak_n >= 2:
            d['streak'] = f"{'🔥' * min(streak_n, 3)} {streak_p}: {streak_n}-turn streak"
        else:
            sorted_totals = sorted(enumerate(totals), key=lambda x: x[1], reverse=True)
            if len(sorted_totals) >= 2:
                leader_i, leader_score = sorted_totals[0]
                second_i, second_score = sorted_totals[1]
                gap = leader_score - second_score
                if gap == 0:
                    d['streak'] = f"📊 {self.players[leader_i]} & {self.players[second_i]} tied!"
                else:
                    d['streak'] = f"📊 {self.players[second_i]} trails {self.players[leader_i]} by {gap} pts"
            else:
                d['streak'] = ""

        self._render_status_bar()

    def update_turn_ui(self):
        curr = self.current_turn_index
        CLR_PENDING = "#7A4800"   # amber-dark for pending reclaim bg
        CLR_PENDING_BORDER = "#FFB300"  # amber highlight

        # Turn label priority: Joker > Correction > Normal
        if self.joker_active:
            self.turn_label.setText(
                "🃏 Joker Rules Active  —  "
                "① Score matching Upper box if open  "
                "② Otherwise score any open Lower box  "
                "③ If all Lower full, take 0 in any Upper box"
            )
            self.turn_label.setStyleSheet(
                f"color: {CLR_ACCENT}; border: 2px solid {CLR_ACCENT}; "
                f"padding: 6px; font-size: 11px;"
            )
        elif self._correction_replaced_msg:
            self.turn_label.setText(self._correction_replaced_msg)
            self.turn_label.setStyleSheet(
                f"color: #4CAF50; border: 2px solid #4CAF50; "
                f"padding: 6px; font-size: 11px;"
            )
        elif self._correction_pending:
            self.turn_label.setText(
                f"⚠️  {self._last_unclaimed_name} unclaimed — fill any box to replace it, then score your turn"
            )
            self.turn_label.setStyleSheet(
                f"color: {CLR_PENDING_BORDER}; border: 2px solid {CLR_PENDING_BORDER}; "
                f"padding: 6px; font-size: 11px;"
            )
        else:
            self.turn_label.setText(f"Active Turn: {self.players[curr]}")
            self.turn_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding: 10px;")

        UPPER_TOOLTIP = "① Joker: score here first if this matches your five-of-a-kind number."
        LOWER_TOOLTIP = "② Joker: score here if your matching Upper box is already claimed."

        for c in range(self.table.columnCount()):
            is_active = (c == curr)
            self.update_yahtzee_bonus_state(c)
            self._update_upper_dropdowns(c)

            for r in range(self.table.rowCount()):
                item, widget = self.table.item(r, c), self.table.cellWidget(r, c)
                if not item or r in CALCULATED_ROWS: continue

                status = item.data(Qt.ItemDataRole.UserRole)
                bg = CLR_TABLE if status == "claimed" else (CLR_ACTIVE_UNCLAIMED if is_active else CLR_UNCLAIMED)

                # JOKER DIMMING LOGIC
                if is_active and self.joker_active and status == "unclaimed":
                    if r not in LOWER_SECTION_PRIMARY and r not in UPPER_SECTION:
                        bg = CLR_DISABLED

                item.setBackground(QColor(bg))
                item.setForeground(QBrush(QColor("#E0E0E0")))

                # Joker tooltips
                if is_active and self.joker_active and status == "unclaimed":
                    if r in UPPER_SECTION:
                        item.setToolTip(UPPER_TOOLTIP)
                        if widget: widget.setToolTip(UPPER_TOOLTIP)
                    elif r in LOWER_SECTION_PRIMARY:
                        item.setToolTip(LOWER_TOOLTIP)
                        if widget: widget.setToolTip(LOWER_TOOLTIP)
                else:
                    item.setToolTip("")
                    if widget: widget.setToolTip("")

                if widget:
                    txt = CLR_CLAIMED_TEXT if status == "claimed" else "white"
                    widget.setStyleSheet(f"background-color: {bg}; color: {txt}; border: none;")
                    if r != 15:  # bonus cell managed exclusively by update_yahtzee_bonus_state
                        widget.setEnabled(is_active)

        self.update_status_bar()

    def update_yahtzee_bonus_state(self, c):
        widget = self.table.cellWidget(15, c)
        if not widget: return
        can_bonus = self.table.item(14, c).text() == "50" and not self.joker_active
        widget.setEnabled(can_bonus and c == self.current_turn_index)
        widget.setStyleSheet(f"background-color: {CLR_ACCENT if can_bonus else CLR_DISABLED};")

    def recalc(self, c):
        u_sum = sum(int(self.table.item(r, c).text()) for r in range(6) if self.table.item(r, c).text().isdigit())
        self.table.item(6, c).setText(str(u_sum))
        bonus = 35 if u_sum >= 63 else 0
        self.table.item(7, c).setText(str(bonus))
        self.table.item(8, c).setText(str(u_sum + bonus))
        l_sum = sum(int(self.table.item(r, c).text()) for r in [9,10,11,12,13,14,16] if self.table.item(r, c).text().isdigit())
        y_bonus = int(self.table.item(15, c).text()) * 100
        self.table.item(17, c).setText(str(l_sum + y_bonus))
        self.table.item(18, c).setText(str(u_sum + bonus + l_sum + y_bonus))

    def check_game_over(self):
        for c in range(self.table.columnCount()):
            if self.player_has_turns_left(c): return

        scores = sorted([(self.players[i], int(self.table.item(18, i).text())) for i in range(len(self.players))], key=lambda x: x[1], reverse=True)
        winner_name, winner_score = scores[0][0], scores[0][1]
        self.save_high_score(winner_name, winner_score)

        dlg = GameOverDialog(scores, self)
        dlg.exec()
        choice = dlg.result_choice
        self.play_again_requested = choice in (GameOverDialog.SAME_ORDER, GameOverDialog.ROLL_ORDER)
        self.roll_for_order = (choice == GameOverDialog.ROLL_ORDER)

        self.close()

    def save_high_score(self, name, score):
        filename = "yahtzee_highscores.json"
        scores_data = []
        
        # Load existing scores if the file exists
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    scores_data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        # Append the new winner
        scores_data.append({
            "name": name,
            "score": score,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Sort descending by score and keep only the top 10
        scores_data = sorted(scores_data, key=lambda x: x["score"], reverse=True)[:10]
        
        # Save back to file
        with open(filename, "w") as f:
            json.dump(scores_data, f, indent=4)
        self._load_alltime_high()

    def show_high_scores(self):
        filename = "yahtzee_highscores.json"
        dialog = QDialog(self)
        dialog.setWindowTitle("Top 10 High Scores")
        dialog.resize(350, 400)
        dialog.setStyleSheet(DARK_STYLESHEET)
        layout = QVBoxLayout(dialog)
        
        if not os.path.exists(filename):
            msg = QLabel("No high scores recorded yet. Go finish a game!")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(msg)
        else:
            try:
                with open(filename, "r") as f:
                    scores_data = json.load(f)
                
                table = QTableWidget(len(scores_data), 3)
                table.setHorizontalHeaderLabels(["Rank", "Player", "Score"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Make read-only
                
                for r, row_data in enumerate(scores_data):
                    table.setItem(r, 0, QTableWidgetItem(f"#{r+1}"))
                    table.setItem(r, 1, QTableWidgetItem(row_data["name"]))
                    table.setItem(r, 2, QTableWidgetItem(str(row_data["score"])))
                    
                layout.addWidget(table)
            except Exception as e:
                layout.addWidget(QLabel(f"Error loading scores: {e}"))
                
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        dialog.exec()

    def reset(self):
        if QMessageBox.question(self, "Reset", "Clear?") == QMessageBox.StandardButton.Yes:
            self.current_turn_index = 0; self.setup_board(); self.update_turn_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)

    ordered_names = None  # set after first rolloff; reused on Same Order

    while True:
        # --- Registration (skipped on Same Order) ---
        if ordered_names is None:
            setup = PlayerSetupDialog()
            if not setup.exec():
                break
            names = [i.text().strip() or f"P{idx+1}" for idx, (_, i) in enumerate(setup.player_inputs)]
        else:
            names = ordered_names  # carry existing players straight to rolloff

        # --- Roll-off ---
        rolloff = RollOffDialog(names)
        if not rolloff.exec():
            break
        ordered_names = rolloff.sorted_names

        # --- Game ---
        w = YahtzeeScorecard(ordered_names)
        w.loop = QEventLoop()
        w.show()
        w.loop.exec()

        if not getattr(w, 'play_again_requested', False):
            sys.exit(0)

        if not getattr(w, 'roll_for_order', False):
            # Same Order: skip registration AND rolloff, restart immediately
            w2_names = ordered_names
            while True:
                w2 = YahtzeeScorecard(w2_names)
                w2.loop = QEventLoop()
                w2.show()
                w2.loop.exec()

                if not getattr(w2, 'play_again_requested', False):
                    sys.exit(0)

                if getattr(w2, 'roll_for_order', False):
                    ordered_names = w2_names  # go to rolloff with these players
                    break
                # else: same order again — keep looping
            # fall through to top of outer loop → rolloff with ordered_names

        # Roll for Order: ordered_names already set, outer loop goes to rolloff
        # (registration skipped because ordered_names is not None)

    sys.exit(0)
