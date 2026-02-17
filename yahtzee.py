#!/usr/bin/env python3

import sys
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                             QScrollArea, QHeaderView, QFileDialog, QComboBox)
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

DARK_STYLESHEET = f"""
    QMainWindow, QDialog, QWidget {{ background-color: {CLR_BACKGROUND}; color: #E0E0E0; }}
    QTableWidget {{ background-color: {CLR_TABLE}; color: #E0E0E0; gridline-color: #333333; border: 1px solid #333333; }}
    QHeaderView::section {{ background-color: #252525; color: #BB86FC; padding: 5px; border: 1px solid #333333; font-weight: bold; }}
    QComboBox {{ background-color: {CLR_UNCLAIMED}; color: white; border: 1px solid #3D3D3D; border-radius: 3px; padding: 2px; }}
    QLineEdit {{ background-color: #2D2D2D; color: white; border: 1px solid #3D3D3D; border-radius: 4px; padding: 5px; }}
    QPushButton {{ background-color: #333333; color: white; border-radius: 4px; padding: 10px; font-weight: bold; }}
    QPushButton:hover {{ background-color: #444444; }}
"""

UPPER_SECTION = [0, 1, 2, 3, 4, 5]
FIXED_SCORE_ROWS = {11: 25, 12: 30, 13: 40, 14: 50}
MANUAL_INPUT_ROWS = [9, 10, 15, 16] 
CALCULATED_ROWS = [6, 7, 8, 17, 18]
PRIMARY_CATEGORIES = [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 16]

ROW_LABELS = (["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"] + 
              ["Sum", "Bonus (35)", "Total Upper"] + 
              ["3 of a Kind", "4 of a Kind", "Full House", "Small Straight", 
               "Large Straight", "Yahtzee", "Yahtzee Bonus (Count)", "Chance"] + 
              ["Total Lower", "GRAND TOTAL"])

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
        self.names = names
        self.player_scores = {name: [] for name in names}
        self.to_roll = list(names)
        self.sorted_names = []
        self.animation_counter = 0
        
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

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_roll)

    def start_animation(self):
        self.btn_roll.setEnabled(False)
        self.animation_counter = 0
        self.timer.start(50)

    def animate_roll(self):
        self.animation_counter += 1
        for name in self.to_roll:
            idx = self.names.index(name)
            temp_roll = sum(random.randint(1, 6) for _ in range(5))
            self.table.item(idx, 1).setText(str(temp_roll))
        if self.animation_counter > 20:
            self.timer.stop()
            self.finalize_roll()

    def finalize_roll(self):
        for name in self.to_roll:
            idx = self.names.index(name)
            final_roll = sum(random.randint(1, 6) for _ in range(5))
            self.player_scores[name].append(final_roll)
            self.table.item(idx, 1).setText(str(final_roll))
        
        all_score_histories = list(self.player_scores.values())
        self.to_roll = [n for n in self.names if all_score_histories.count(self.player_scores[n]) > 1]

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
        self.players = players
        self.current_turn_index = 0
        self.play_again_requested = False
        self._is_updating = False  # Re-entrancy guard
        self.setWindowTitle("Yahtzee! Pro Scorecard")
        self.resize(1100, 900)
        
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        
        self.turn_label = QLabel("")
        self.turn_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.turn_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding: 10px;")
        layout.addWidget(self.turn_label)

        self.table = QTableWidget(len(ROW_LABELS), len(players))
        self.table.setVerticalHeaderLabels(ROW_LABELS)
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setup_board()
        self.table.itemChanged.connect(self.handle_manual_entry)
        layout.addWidget(self.table)
        
        btns = QHBoxLayout()
        export = QPushButton("Export Results")
        reset = QPushButton("Reset Game")
        export.clicked.connect(self.export_txt)
        reset.clicked.connect(self.reset)
        btns.addWidget(export)
        btns.addWidget(reset)
        layout.addLayout(btns)
        self.update_turn_ui()

    def setup_board(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = QTableWidgetItem("-")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, "unclaimed")
                if r in CALCULATED_ROWS:
                    item.setText("0")
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(QColor(CLR_TOTAL_BG))
                    item.setForeground(QBrush(QColor(CLR_ACCENT)))
                elif r in UPPER_SECTION:
                    self.add_dropdown(r, c, ["-", "0", "1", "2", "3", "4", "5"])
                elif r in FIXED_SCORE_ROWS:
                    self.add_dropdown(r, c, ["-", "✓", "0"])
                else:
                    item.setBackground(QColor(CLR_UNCLAIMED))
                self.table.setItem(r, c, item)
        self.table.blockSignals(False)

    def add_dropdown(self, r, c, options):
        combo = QComboBox()
        combo.addItems(options)
        combo.setProperty("row", r)
        combo.setProperty("col", c)
        combo.currentIndexChanged.connect(self.handle_dropdown)
        self.table.setCellWidget(r, c, combo)

    def handle_dropdown(self, index):
        if self._is_updating: return
        combo = self.sender()
        r, c = combo.property("row"), combo.property("col")
        text = combo.currentText()
        if text == "-": return

        # Confirm if editing out of turn
        if c != self.current_turn_index:
            reply = QMessageBox.question(self, 'Confirm Entry', 
                f"It is {self.players[self.current_turn_index]}'s turn.\nUpdate score for {self.players[c]} anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                self.table.blockSignals(True)
                combo.setCurrentIndex(0)
                self.table.blockSignals(False)
                return

        self._is_updating = True
        self.table.blockSignals(True)
        
        item = self.table.item(r, c)
        is_new = item.data(Qt.ItemDataRole.UserRole) == "unclaimed"
        score = (int(text) * (r + 1)) if r in UPPER_SECTION else (FIXED_SCORE_ROWS[r] if text == "✓" else 0)
        
        item.setText(str(score))
        item.setData(Qt.ItemDataRole.UserRole, "claimed")

        # Special logic for Yahtzee Bonus auto-fill
        if r == 14: 
            bonus_item = self.table.item(15, c)
            if score == 0:
                bonus_item.setText("0")
                bonus_item.setData(Qt.ItemDataRole.UserRole, "claimed")
                bonus_item.setFlags(Qt.ItemFlag.NoItemFlags)
                bonus_item.setBackground(QColor(CLR_DISABLED)) 
            else:
                bonus_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                bonus_item.setBackground(QColor(CLR_UNCLAIMED))
        
        self.recalc(c)
        
        # Advance turn only after successful logic and only if current player finished a new slot
        if is_new and c == self.current_turn_index:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            
        self.table.blockSignals(False)
        self.update_turn_ui()
        self._is_updating = False

    def handle_manual_entry(self, item):
        if self._is_updating or item.row() not in MANUAL_INPUT_ROWS or item.text() == "-": 
            return
        
        r, c = item.row(), item.column()

        # 1. Turn Check
        if c != self.current_turn_index:
            reply = QMessageBox.question(self, 'Confirm Entry', 
                f"It is {self.players[self.current_turn_index]}'s turn.\nUpdate score for {self.players[c]} anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                self.table.blockSignals(True)
                item.setText("-")
                self.table.blockSignals(False)
                return

        # 2. Validation
        self._is_updating = True
        self.table.blockSignals(True)
        
        try:
            val = int(item.text())
            valid = False
            if r in [9, 10, 16]: # 3ofK, 4ofK, Chance
                if val == 0 or (5 <= val <= 30): valid = True
            elif r == 15: # Yahtzee Bonus
                if 0 <= val <= 12: valid = True

            if valid:
                is_new = item.data(Qt.ItemDataRole.UserRole) == "unclaimed"
                item.setData(Qt.ItemDataRole.UserRole, "claimed")
                self.recalc(c)
                # Advance turn only for new valid entries by the active player
                if is_new and r != 15 and c == self.current_turn_index:
                    self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            else:
                QMessageBox.warning(self, "Invalid Score", 
                    f"'{val}' is mathematically impossible for {ROW_LABELS[r]}.\n"
                    "Allowed values: 5-30 or 0 (to scratch).")
                item.setText("-")
                item.setData(Qt.ItemDataRole.UserRole, "unclaimed") # Reset to allow retry
        except ValueError:
            item.setText("-")
            
        self.table.blockSignals(False)
        self.update_turn_ui()
        self._is_updating = False

    def update_turn_ui(self):
        self.turn_label.setText(f"Active Turn: {self.players[self.current_turn_index]}")
        for c in range(self.table.columnCount()):
            is_active_col = (c == self.current_turn_index)
            name = f"▶ {self.players[c]}" if is_active_col else self.players[c]
            h_item = QTableWidgetItem(name)
            h_item.setForeground(QBrush(QColor(CLR_ACTIVE_TURN if is_active_col else "#555555")))
            self.table.setHorizontalHeaderItem(c, h_item)
            for r in range(self.table.rowCount()):
                if r in CALCULATED_ROWS: continue
                item = self.table.item(r, c)
                status = item.data(Qt.ItemDataRole.UserRole)
                widget = self.table.cellWidget(r, c)
                if status == "unclaimed":
                    bg = CLR_ACTIVE_UNCLAIMED if is_active_col else CLR_UNCLAIMED
                    item.setBackground(QColor(bg))
                    if widget: widget.setStyleSheet(f"background-color: {bg}; color: white; border: none;")
                else:
                    item.setBackground(QColor(CLR_TABLE))
                    item.setForeground(QBrush(QColor(CLR_CLAIMED_TEXT)))
                    if widget: widget.setStyleSheet(f"background-color: {CLR_TABLE}; color: {CLR_CLAIMED_TEXT}; font-weight: bold; border: none;")

    def recalc(self, c):
        u_sum = sum(int(self.table.item(r, c).text()) for r in range(6) if self.table.item(r, c).text().isdigit())
        self.table.item(6, c).setText(str(u_sum))
        bonus = 35 if u_sum >= 63 else 0
        self.table.item(7, c).setText(str(bonus))
        self.table.item(8, c).setText(str(u_sum + bonus))
        l_sum = sum(int(self.table.item(r, c).text()) for r in [9, 10, 11, 12, 13, 14, 16] if self.table.item(r, c).text().isdigit())
        y_bonus = (int(self.table.item(15, c).text()) * 100) if self.table.item(15, c).text().isdigit() else 0
        self.table.item(17, c).setText(str(l_sum + y_bonus))
        self.table.item(18, c).setText(str(u_sum + bonus + l_sum + y_bonus))
        self.check_game_over()

    def check_game_over(self):
        for c in range(self.table.columnCount()):
            for r in PRIMARY_CATEGORIES:
                if self.table.item(r, c).text() == "-": return
        
        scores = [(self.players[i], int(self.table.item(18, i).text())) for i in range(len(self.players))]
        scores.sort(key=lambda x: x[1], reverse=True)
        winner_text = f"🏆 Winner: {scores[0][0]} ({scores[0][1]} pts)"
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Game Over")
        msg.setText(winner_text)
        btn_play = msg.addButton("Play Again", QMessageBox.ButtonRole.AcceptRole)
        btn_exit = msg.addButton("Exit", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        
        if msg.clickedButton() == btn_play:
            self.play_again_requested = True
            self.close()
        else:
            self.close()

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Scorecard", "", "Text Files (*.txt)")
        if path:
            with open(path, 'w') as f:
                for r in range(len(ROW_LABELS)):
                    row_data = [self.table.item(r, c).text() for c in range(len(self.players))]
                    f.write(f"{ROW_LABELS[r]:<20} | {' | '.join(row_data)}\n")

    def reset(self):
        if QMessageBox.question(self, "Reset", "Clear scores?") == QMessageBox.StandardButton.Yes:
            self.current_turn_index = 0
            self.setup_board()
            self.update_turn_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    setup = PlayerSetupDialog()
    if setup.exec():
        names = [i.text().strip() or f"P{idx+1}" for idx, (_, i) in enumerate(setup.player_inputs)]
        while True:
            rolloff = RollOffDialog(names)
            if rolloff.exec() == QDialog.DialogCode.Accepted:
                w = YahtzeeScorecard(rolloff.sorted_names)
                w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                w.show()
                loop = QEventLoop()
                w.destroyed.connect(loop.quit)
                loop.exec()
                if not getattr(w, 'play_again_requested', False): break
            else: break
