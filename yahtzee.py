#!/usr/bin/env python3

import sys
import random
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
        self.resize(600, 700)
        layout = QVBoxLayout(self)
        rules_text = QTextEdit()
        rules_text.setReadOnly(True)
        rules_text.setHtml("""
            <h2 style='color: #03DAC6;'>Yahtzee Rules</h2>
            <h3 style='color: #BB86FC;'>Joker Rule Logic</h3>
            <p>When you roll a Yahtzee and your Yahtzee box is already filled with a 50:</p>
            <ol>
                <li><b>Score the Bonus:</b> Click the '+' for 100 points.</li>
                <li><b>Mandatory Upper:</b> If the matching number in the Upper Section is open, you MUST score there.</li>
                <li><b>Joker Choice:</b> If that Upper box is full, you may score in any empty Lower box for full points (e.g. 40 for Large Straight).</li>
                <li><b>Last Resort:</b> If all Lower boxes are full, you must score a zero in an open Upper box.</li>
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
        export, reset, rules = QPushButton("Export"), QPushButton("Reset"), QPushButton("Rules")
        export.clicked.connect(self.export_txt); reset.clicked.connect(self.reset); rules.clicked.connect(self.show_rules)
        btns.addWidget(export); btns.addWidget(reset); btns.addWidget(rules)
        layout.addLayout(btns)
        
        self.update_turn_ui()

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
            self.turn_label.setText("JOKER ACTIVE: Select matching Upper box. If full, select any Lower box.")
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
        scores = sorted([(self.players[i], int(self.table.item(18, i).text())) for i in range(len(self.players))], key=lambda x: x[1], reverse=True)
        res = QMessageBox.question(self, "Game Over", f"Winner: {scores[0][0]} ({scores[0][1]} pts)\nPlay Again?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes: self.play_again_requested = True
        self.close()

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "Text Files (*.txt)")
        if path:
            with open(path, 'w') as f:
                for r in range(len(ROW_LABELS)):
                    f.write(f"{ROW_LABELS[r]:<20} | {' | '.join([self.table.item(r, c).text() for c in range(len(self.players))])}\n")

    def reset(self):
        if QMessageBox.question(self, "Reset", "Clear?") == QMessageBox.StandardButton.Yes:
            self.current_turn_index = 0; self.setup_board(); self.update_turn_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyleSheet(DARK_STYLESHEET)
    while True:
        setup = PlayerSetupDialog()
        if setup.exec():
            names = [i.text().strip() or f"P{idx+1}" for idx, (_, i) in enumerate(setup.player_inputs)]
            rolloff = RollOffDialog(names)
            if rolloff.exec():
                w = YahtzeeScorecard(rolloff.sorted_names)
                w.loop = QEventLoop(); w.show(); w.loop.exec()
                if not getattr(w, 'play_again_requested', False): break
            else: break
        else: break
