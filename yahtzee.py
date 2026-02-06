#!/usr/bin/env python3

import sys
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                             QScrollArea, QHeaderView, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush

# --- Theme Configuration ---
CLR_BACKGROUND = "#121212"
CLR_TABLE = "#1E1E1E"
CLR_UNCLAIMED = "#2A2A2A"
CLR_ERROR = "#660000"
CLR_TOTAL_BG = "#000000"
CLR_ACCENT = "#03DAC6"     # Teal
CLR_CLAIMED_TEXT = "#BB86FC" # Purple
CLR_ACTIVE_TURN = "#FFD700"  # Gold

DARK_STYLESHEET = f"""
    QMainWindow, QDialog, QWidget {{ background-color: {CLR_BACKGROUND}; color: #E0E0E0; }}
    QTableWidget {{ background-color: {CLR_TABLE}; color: #E0E0E0; gridline-color: #333333; border: 1px solid #333333; }}
    QHeaderView::section {{ background-color: #252525; color: #BB86FC; padding: 5px; border: 1px solid #333333; font-weight: bold; }}
    QComboBox {{ background-color: {CLR_UNCLAIMED}; color: white; border: 1px solid #3D3D3D; border-radius: 3px; padding: 2px; }}
    QPushButton {{ background-color: #333333; color: white; border-radius: 4px; padding: 10px; font-weight: bold; }}
    QPushButton:hover {{ background-color: #444444; }}
"""

# --- Mapping ---
UPPER_SECTION = [0, 1, 2, 3, 4, 5]
CALCULATED_ROWS = [6, 7, 8, 17, 18]
FIXED_SCORE_ROWS = {11: 25, 12: 30, 13: 40, 14: 50}
MANUAL_INPUT_ROWS = [9, 10, 15, 16] # 3 of Kind, 4 of Kind, Bonus Yahtzee Count, Chance

ROW_LABELS = (["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"] + 
              ["Sum", "Bonus (35)", "Total Upper"] + 
              ["3 of a Kind", "4 of a Kind", "Full House", "Small Straight", 
               "Large Straight", "Yahtzee", "Yahtzee Bonus (Count)", "Chance"] + 
              ["Total Lower", "GRAND TOTAL"])

class RollOffDialog(QDialog):
    def __init__(self, names):
        super().__init__()
        self.setWindowTitle("Roll-Off for Order")
        self.setFixedSize(450, 500)
        self.names = names
        self.sorted_names = []
        self.animation_counter = 0
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🎲 Rolling 5 dice per player..."))
        self.table = QTableWidget(len(names), 2)
        self.table.setHorizontalHeaderLabels(["Player", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i, name in enumerate(names):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem("-"))
        layout.addWidget(self.table)
        self.btn_roll = QPushButton("Roll Dice"); self.btn_roll.clicked.connect(self.start_animation); layout.addWidget(self.btn_roll)
        self.btn_start = QPushButton("Start Game"); self.btn_start.setEnabled(False); self.btn_start.clicked.connect(self.accept); layout.addWidget(self.btn_start)
        self.timer = QTimer(); self.timer.timeout.connect(self.animate)

    def start_animation(self):
        self.btn_roll.setEnabled(False); self.animation_counter = 0; self.timer.start(50)

    def animate(self):
        self.animation_counter += 1
        for i in range(len(self.names)): self.table.item(i, 1).setText(str(sum(random.randint(1,6) for _ in range(5))))
        if self.animation_counter > 20:
            self.timer.stop(); self.finalize()

    def finalize(self):
        rolls = []
        for i, name in enumerate(self.names):
            val = sum(random.randint(1,6) for _ in range(5))
            self.table.item(i, 1).setText(str(val)); self.table.item(i, 1).setForeground(QBrush(QColor(CLR_ACTIVE_TURN)))
            rolls.append((name, val))
        rolls.sort(key=lambda x: x[1], reverse=True)
        self.sorted_names = [r[0] for r in rolls]
        self.btn_start.setEnabled(True); self.btn_start.setStyleSheet(f"background-color: {CLR_ACCENT}; color: black;")

class YahtzeeScorecard(QMainWindow):
    def __init__(self, players):
        super().__init__()
        self.players = players
        self.current_turn_index = 0
        self.setWindowTitle("Yahtzee! Pro Scorecard")
        self.resize(1100, 900)
        
        container = QWidget(); self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        
        self.turn_label = QLabel(f"Current Turn: {self.players[0]}")
        self.turn_label.setFont(QFont("Arial", 14, QFont.Weight.Bold)); self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.turn_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; margin: 10px;")
        layout.addWidget(self.turn_label)

        self.table = QTableWidget(len(ROW_LABELS), len(players))
        self.table.setVerticalHeaderLabels(ROW_LABELS); self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setup_board()
        self.table.itemChanged.connect(self.handle_manual_entry)
        layout.addWidget(self.table)
        
        btns = QHBoxLayout(); export = QPushButton("Export Results"); reset = QPushButton("Reset Game")
        export.clicked.connect(self.export_txt); reset.clicked.connect(self.reset)
        btns.addWidget(export); btns.addWidget(reset); layout.addLayout(btns)
        self.update_ui()

    def setup_board(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = QTableWidgetItem("-")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, "unclaimed") # Strict state tracking
                
                if r in CALCULATED_ROWS:
                    item.setText("0"); item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(QColor(CLR_TOTAL_BG)); item.setForeground(QBrush(QColor(CLR_ACCENT)))
                
                elif r in UPPER_SECTION:
                    self.add_dropdown(r, c, ["-", "0", "1", "2", "3", "4", "5"])
                
                elif r in FIXED_SCORE_ROWS:
                    self.add_dropdown(r, c, ["-", "✓", "0"])
                
                else: # Manual (Chance, X of a Kind)
                    item.setBackground(QColor(CLR_UNCLAIMED))
                
                self.table.setItem(r, c, item)
        self.table.blockSignals(False)

    def add_dropdown(self, r, c, options):
        combo = QComboBox()
        combo.addItems(options)
        combo.setProperty("row", r); combo.setProperty("col", c)
        combo.currentIndexChanged.connect(self.handle_dropdown)
        self.table.setCellWidget(r, c, combo)

    def handle_dropdown(self, index):
        combo = self.sender()
        r, c = combo.property("row"), combo.property("col")
        text = combo.currentText()
        item = self.table.item(r, c)
        
        self.table.blockSignals(True)
        if text == "-":
            item.setText("-"); item.setData(Qt.ItemDataRole.UserRole, "unclaimed")
            combo.setStyleSheet("")
        else:
            is_new = item.data(Qt.ItemDataRole.UserRole) == "unclaimed"
            if r in UPPER_SECTION: score = int(text) * (r + 1)
            else: score = FIXED_SCORE_ROWS[r] if text == "✓" else 0
            
            item.setText(str(score)); item.setData(Qt.ItemDataRole.UserRole, "claimed")
            combo.setStyleSheet(f"background-color: {CLR_TABLE}; color: {CLR_CLAIMED_TEXT}; font-weight: bold;")
            if is_new: self.advance_turn(c)
        
        self.recalc(c); self.table.blockSignals(False)

    def handle_manual_entry(self, item):
        r, c = item.row(), item.column()
        if r not in MANUAL_INPUT_ROWS: return
        
        text = item.text()
        if text == "-": return

        self.table.blockSignals(True)
        try:
            val = int(text)
            is_new = item.data(Qt.ItemDataRole.UserRole) == "unclaimed"
            item.setData(Qt.ItemDataRole.UserRole, "claimed")
            item.setBackground(QColor(CLR_TABLE)); item.setForeground(QBrush(QColor(CLR_CLAIMED_TEXT)))
            if is_new: self.advance_turn(c)
        except ValueError:
            item.setText("-")
        
        self.recalc(c); self.table.blockSignals(False)

    def advance_turn(self, col):
        # Only advance if the active player filled THEIR column
        if col == self.current_turn_index:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            self.update_ui()

    def update_ui(self):
        self.turn_label.setText(f"Current Turn: {self.players[self.current_turn_index]}")
        for i in range(len(self.players)):
            name = f"▶ {self.players[i]}" if i == self.current_turn_index else self.players[i]
            h_item = QTableWidgetItem(name)
            h_item.setForeground(QBrush(QColor(CLR_ACTIVE_TURN if i == self.current_turn_index else CLR_CLAIMED_TEXT)))
            self.table.setHorizontalHeaderItem(i, h_item)

    def recalc(self, c):
        u_sum = sum(int(self.table.item(r, c).text()) for r in range(6) if self.table.item(r, c).text().isdigit())
        bonus = 35 if u_sum >= 63 else 0
        self.table.item(6, c).setText(str(u_sum))
        self.table.item(7, c).setText(str(bonus))
        self.table.item(8, c).setText(str(u_sum + bonus))
        
        l_rows = [9, 10, 11, 12, 13, 14, 16]
        l_sum = sum(int(self.table.item(r, c).text()) for r in l_rows if self.table.item(r, c).text().isdigit())
        l_sum += (int(self.table.item(15, c).text()) * 100 if self.table.item(15, c).text().isdigit() else 0)
        
        self.table.item(17, c).setText(str(l_sum))
        self.table.item(18, c).setText(str(u_sum + bonus + l_sum))
        self.check_win()

    def check_win(self):
        for c in range(self.table.columnCount()):
            for r in [0,1,2,3,4,5,9,10,11,12,13,14,15,16]:
                if self.table.item(r, c).text() == "-": return
        scores = [(self.players[i], int(self.table.item(18, i).text())) for i in range(len(self.players))]
        scores.sort(key=lambda x: x[1], reverse=True)
        QMessageBox.information(self, "Game Over", f"Winner: {scores[0][0]} with {scores[0][1]} points!")

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Scorecard", "", "Text Files (*.txt)")
        if path:
            with open(path, 'w') as f:
                for r in range(len(ROW_LABELS)):
                    row_data = [self.table.item(r, c).text() for c in range(len(self.players))]
                    f.write(f"{ROW_LABELS[r]:<20} | {' | '.join(row_data)}\n")

    def reset(self):
        if QMessageBox.question(self, "Reset", "Clear all scores?") == QMessageBox.StandardButton.Yes:
            self.current_turn_index = 0; self.setup_board(); self.update_ui()

class PlayerSetup(QDialog):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Yahtzee Registration"); self.setFixedSize(300, 400)
        self.inputs = []; layout = QVBoxLayout(self)
        self.scroll = QScrollArea(); widget = QWidget(); self.vbox = QVBoxLayout(widget)
        self.scroll.setWidget(widget); self.scroll.setWidgetResizable(True); layout.addWidget(self.scroll)
        add = QPushButton("Add Player"); add.clicked.connect(self.add_p); layout.addWidget(add)
        go = QPushButton("Next"); go.clicked.connect(self.accept); layout.addWidget(go)
        self.add_p()

    def add_p(self):
        if len(self.inputs) < 8:
            i = QLineEdit(); i.setPlaceholderText(f"Player {len(self.inputs)+1}")
            self.inputs.append(i); self.vbox.addWidget(i)

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyleSheet(DARK_STYLESHEET)
    s = PlayerSetup()
    if s.exec():
        names = [i.text().strip() or f"P{idx+1}" for idx, i in enumerate(s.inputs)]
        r = RollOffDialog(names)
        if r.exec():
            w = YahtzeeScorecard(r.sorted_names); w.show(); sys.exit(app.exec())
