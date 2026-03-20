#!/usr/bin/env python3

import sys
import random
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                             QScrollArea, QHeaderView, QFileDialog, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QEventLoop
from PyQt6.QtGui import QColor, QFont, QBrush

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
            <h2 style='color: #03DAC6;'>Official Yahtzee Rules</h2>

            <h3 style='color: #BB86FC;'>Object of the Game</h3>
            <p>Obtain the highest score for one or more games. The player with the highest total score for all games (up to 6 games) wins.</p>

            <h3 style='color: #BB86FC;'>How to Play</h3>
            <p>Each player rolls all five dice to determine who goes first — highest total starts. Play continues clockwise.</p>
            <p>Each turn consists of a maximum of <b>three rolls</b>. The first roll must use all five dice. On the second and third rolls, the player may set aside any dice and re-roll the rest. After the final roll, the player <b>must</b> enter a score (or a zero) in one open box.</p>

            <h3 style='color: #BB86FC;'>Upper Section</h3>
            <p>Score <b>only</b> the dice matching that category's number. For example, rolling three 3s scores 9 in the Threes box.</p>
            <ul>
                <li><b>Ones</b> — sum of all 1s</li>
                <li><b>Twos</b> — sum of all 2s</li>
                <li><b>Threes</b> — sum of all 3s</li>
                <li><b>Fours</b> — sum of all 4s</li>
                <li><b>Fives</b> — sum of all 5s</li>
                <li><b>Sixes</b> — sum of all 6s</li>
            </ul>
            <p><b>Bonus:</b> Score 63 or more in the Upper Section to earn a <b>+35 bonus</b>. (Tip: scoring three of each number adds up to exactly 63.)</p>

            <h3 style='color: #BB86FC;'>Lower Section</h3>
            <ul>
                <li><b>3 of a Kind</b> — at least three dice the same; score = total of <i>all</i> dice</li>
                <li><b>4 of a Kind</b> — at least four dice the same; score = total of <i>all</i> dice</li>
                <li><b>Full House</b> — three of one number and two of another; scores <b>25 points</b></li>
                <li><b>Small Straight</b> — any four sequential numbers (e.g. 1-2-3-4); scores <b>30 points</b></li>
                <li><b>Large Straight</b> — five sequential numbers (1-2-3-4-5 or 2-3-4-5-6); scores <b>40 points</b></li>
                <li><b>Yahtzee</b> — five of a kind; scores <b>50 points</b></li>
                <li><b>Chance</b> — any combination; score = total of <i>all</i> dice</li>
            </ul>

            <h3 style='color: #BB86FC;'>Yahtzee Bonus</h3>
            <p>If you roll a second (or further) Yahtzee in the same game <b>and</b> your Yahtzee box already holds a 50, you earn a <b>Yahtzee Bonus Chip worth 100 points</b>. Click the <b>+</b> button to record each bonus Yahtzee.</p>
            <p>The second Yahtzee must first be scored in the matching Upper Section box. If that box is already filled, the Joker rules below apply.</p>

            <hr style='border-color: #444;'/>
            <h3 style='color: #BB86FC;'>&#127183; Joker Rules</h3>
            <p>A Yahtzee acts as a <b>Joker</b> only when <i>both</i> conditions are met:</p>
            <ol>
                <li>The Yahtzee box has already been filled (with 50 <i>or</i> 0).</li>
                <li>The matching Upper Section box is already filled.</li>
            </ol>
            <p>When both conditions are met, score in the Lower Section as follows:</p>
            <ul>
                <li><b>3 of a Kind, 4 of a Kind, or Chance</b> — score the total of all 5 dice</li>
                <li><b>Full House</b> — score 25 points</li>
                <li><b>Small Straight</b> — score 30 points</li>
                <li><b>Large Straight</b> — score 40 points</li>
            </ul>
            <p>If all Lower Section boxes are also filled, you must enter a <b>zero</b> in any open Upper Section box. You still receive the Bonus Chip.</p>

            <h3 style='color: #BB86FC;'>In This App — Joker Turn Order</h3>
            <ol>
                <li><b>Score the Bonus:</b> Click <b>+</b> for 100 points (if first Yahtzee scored 50).</li>
                <li><b>Mandatory Upper:</b> If the matching Upper box is open, you <b>must</b> score there.</li>
                <li><b>Joker Choice:</b> If that Upper box is full, score in any open Lower box for full fixed points.</li>
                <li><b>Last Resort:</b> If all Lower boxes are full, enter a zero in any open Upper box.</li>
            </ol>
        """)
        layout.addWidget(rules_text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

class PlayerSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yahtzee Registration")
        self.setFixedSize(400, 500)
        self.player_inputs = [] 
        layout = QVBoxLayout(self)
        header = QLabel("Player Registration")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.input_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
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
        self.next_btn.setStyleSheet(f"background-color: {CLR_ACCENT}; color: black;")
        self.next_btn.clicked.connect(self.accept)
        layout.addWidget(self.next_btn)

    def add_player_slot(self):
        if len(self.player_inputs) < 8:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            inp = QLineEdit()
            inp.setPlaceholderText(f"Player {len(self.player_inputs) + 1}")
            row_layout.addWidget(inp)
            self.input_layout.addWidget(row_widget)
            self.player_inputs.append((row_widget, inp))

    def remove_player_slot(self):
        if len(self.player_inputs) > 1:
            row_widget, _ = self.player_inputs.pop()
            row_widget.deleteLater()

class RollOffDialog(QDialog):
    def __init__(self, names):
        super().__init__()
        self.setWindowTitle("Roll-Off for Order")
        self.setFixedSize(450, 550)
        self.names, self.player_scores = names, {name: [] for name in names}
        self.to_roll, self.sorted_names, self.animation_counter = list(names), [], 0
        layout = QVBoxLayout(self)
        self.info_lbl = QLabel("Rolling 5 dice to determine play order...")
        layout.addWidget(self.info_lbl)
        self.table = QTableWidget(len(names), 2)
        self.table.setHorizontalHeaderLabels(["Player", "Roll Result"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i, name in enumerate(names):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            score_item = QTableWidgetItem("-")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, score_item)
        layout.addWidget(self.table)
        self.btn_roll = QPushButton("🎲 Roll for All Players")
        self.btn_roll.setStyleSheet(f"background-color: {CLR_ACCENT}; color: black;")
        self.btn_roll.clicked.connect(self.start_animation)
        layout.addWidget(self.btn_roll)
        self.btn_start = QPushButton("Start Scoring")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.accept)
        layout.addWidget(self.btn_start)
        self.timer = QTimer(); self.timer.timeout.connect(self.animate_roll)

    def start_animation(self):
        self.btn_roll.setEnabled(False)
        self.animation_counter = 0
        self.timer.start(50)

    def animate_roll(self):
        self.animation_counter += 1
        for name in self.to_roll:
            idx = self.names.index(name)
            self.table.item(idx, 1).setText(str(sum(random.randint(1, 6) for _ in range(5))))
        if self.animation_counter > 20:
            self.timer.stop()
            self.finalize_roll()

    def finalize_roll(self):
        for name in self.to_roll:
            idx, roll = self.names.index(name), sum(random.randint(1, 6) for _ in range(5))
            self.player_scores[name].append(roll)
            self.table.item(idx, 1).setText(str(roll))
        hist = list(self.player_scores.values())
        self.to_roll = [n for n in self.names if hist.count(self.player_scores[n]) > 1]
        if not self.to_roll:
            self.sorted_names = sorted(self.names, key=lambda n: self.player_scores[n], reverse=True)
            self.btn_start.setEnabled(True)
            self.btn_start.setStyleSheet(f"background-color: {CLR_ACCENT}; color: black;")
        else:
            self.btn_roll.setEnabled(True)
            self.btn_roll.setText(f"🎲 Resolve Tie ({len(self.to_roll)} players)")

class YahtzeeScorecard(QMainWindow):
    def __init__(self, players):
        super().__init__()
        self.players, self.current_turn_index, self.play_again_requested, self._is_updating = players, 0, False, False
        self.joker_active = False # Sticky Joker Rule Flag
        
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

    def handle_dropdown(self, index):
        if self._is_updating: return
        combo = self.sender()
        r, c = combo.property("row"), combo.property("col")
        if combo.currentText() == "-": return

        self._is_updating = True
        item = self.table.item(r, c)
        score = int(combo.currentText()) * (r + 1) if r in UPPER_SECTION else int(combo.currentText())
        item.setText(str(score))
        item.setData(Qt.ItemDataRole.UserRole, "claimed")
        
        self.recalc(c)
        self.advance_to_next_player() 
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
        
        self.joker_active = True
        self.recalc(c)
        self.update_turn_ui()

    def advance_to_next_player(self):
        self.joker_active = False # Reset sticky flag
        total = len(self.players)
        for _ in range(total):
            self.current_turn_index = (self.current_turn_index + 1) % total
            if self.player_has_turns_left(self.current_turn_index):
                self.update_turn_ui()
                return
        self.check_game_over()

    def player_has_turns_left(self, c):
        return any(self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "unclaimed" for r in PRIMARY_CATEGORIES)

    def update_turn_ui(self):
        curr = self.current_turn_index
        # Sticky Message Logic
        if self.joker_active:
            self.turn_label.setText("Joker Rules apply!")
            self.turn_label.setStyleSheet(f"color: {CLR_ACCENT}; border: 2px solid {CLR_ACCENT}; padding: 5px;")
        else:
            self.turn_label.setText(f"Active Turn: {self.players[curr]}")
            self.turn_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding: 10px;")

        for c in range(self.table.columnCount()):
            is_active = (c == curr)
            self.update_yahtzee_bonus_state(c)
            
            for r in range(self.table.rowCount()):
                item, widget = self.table.item(r, c), self.table.cellWidget(r, c)
                if not item or r in CALCULATED_ROWS: continue
                
                status = item.data(Qt.ItemDataRole.UserRole)
                bg = CLR_TABLE if status == "claimed" else (CLR_ACTIVE_UNCLAIMED if is_active else CLR_UNCLAIMED)
                
                # JOKER DIMMING LOGIC
                if is_active and self.joker_active and status == "unclaimed":
                    # In a real game, the code would know the dice. Here we dim based on Joker Rule context:
                    # Lower Section becomes the "Joker" playground.
                    if r not in LOWER_SECTION_PRIMARY and r not in UPPER_SECTION:
                        bg = CLR_DISABLED
                
                item.setBackground(QColor(bg))
                if widget:
                    txt = CLR_CLAIMED_TEXT if status == "claimed" else "white"
                    widget.setStyleSheet(f"background-color: {bg}; color: {txt}; border: none;")
                    widget.setEnabled(is_active)

    def update_yahtzee_bonus_state(self, c):
        widget = self.table.cellWidget(15, c)
        if not widget: return
        can_bonus = self.table.item(14, c).text() == "50"
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
            
        # Calculate final scores
        scores = sorted([(self.players[i], int(self.table.item(18, i).text())) for i in range(len(self.players))], key=lambda x: x[1], reverse=True)
        
        # Save the winner's stats automatically
        winner_name, winner_score = scores[0][0], scores[0][1]
        self.save_high_score(winner_name, winner_score)
        
        res = QMessageBox.question(self, "Game Over", f"Winner: {winner_name} ({winner_score} pts)\nPlay Again?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes: 
            self.play_again_requested = True
            
        # Close the window cleanly
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
    
    while True:
        setup = PlayerSetupDialog()
        if not setup.exec(): # User closed the dialog manually
            break
            
        names = [i.text().strip() or f"P{idx+1}" for idx, (_, i) in enumerate(setup.player_inputs)]
        rolloff = RollOffDialog(names)
        
        if not rolloff.exec(): # User closed the dialog manually
            break
            
        w = YahtzeeScorecard(rolloff.sorted_names)
        w.loop = QEventLoop()
        w.show()
        w.loop.exec()
        
        if not getattr(w, 'play_again_requested', False): 
            break
            
    sys.exit(0)
