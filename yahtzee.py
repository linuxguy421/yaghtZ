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
    QMainWindow, QDialog, QWidget {{ 
        background-color: {CLR_BACKGROUND}; 
        color: #E0E0E0; 
    }}
    QTableWidget {{ 
        background-color: {CLR_TABLE}; 
        color: #E0E0E0; 
        gridline-color: #333333; 
        border: 1px solid #333333; 
    }}
    QHeaderView::section {{ 
        background-color: #252525; 
        color: #BB86FC; 
        padding: 5px; 
        border: 1px solid #333333; 
        font-weight: bold;
    }}
    QComboBox {{
        background-color: {CLR_UNCLAIMED};
        color: white;
        border: 1px solid #3D3D3D;
        border-radius: 3px;
        padding: 2px;
    }}
    QPushButton {{ 
        background-color: #333333; 
        color: white; 
        border-radius: 4px;
        padding: 10px; 
        font-weight: bold; 
    }}
    QPushButton:hover {{ background-color: #444444; }}
"""

# --- Game Data ---
ROW_LABELS = (["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"] + 
              ["Sum", "Bonus (35)", "Total Upper"] + 
              ["3 of a Kind", "4 of a Kind", "Full House", "Small Straight", 
               "Large Straight", "Yahtzee", "Yahtzee Bonus (Count)", "Chance"] + 
              ["Total Lower", "GRAND TOTAL"])

FIXED_SCORE_VALUES = {11: 25, 12: 30, 13: 40, 14: 50}
CALCULATED_ROWS = [6, 7, 8, 17, 18]
INPUT_ROWS = [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16]

class RollOffDialog(QDialog):
    def __init__(self, names):
        super().__init__()
        self.setWindowTitle("Roll-Off for Order")
        self.setFixedSize(450, 550)
        self.names = names
        self.sorted_names = []
        self.animation_counter = 0
        
        layout = QVBoxLayout(self)
        lbl = QLabel("Rolling 5 dice to determine play order...")
        lbl.setFont(QFont("Arial", 11))
        layout.addWidget(lbl)

        self.table = QTableWidget(len(names), 2)
        self.table.setHorizontalHeaderLabels(["Player", "Current Roll"])
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
        for i in range(len(self.names)):
            temp_roll = sum(random.randint(1, 6) for _ in range(5))
            self.table.item(i, 1).setText(str(temp_roll))
        if self.animation_counter > 25:
            self.timer.stop()
            self.finalize_roll()

    def finalize_roll(self):
        roll_data = []
        for i, name in enumerate(self.names):
            final_roll = sum(random.randint(1, 6) for _ in range(5))
            self.table.item(i, 1).setText(str(final_roll))
            self.table.item(i, 1).setForeground(QBrush(QColor(CLR_ACTIVE_TURN)))
            roll_data.append((name, final_roll))

        roll_data.sort(key=lambda x: x[1], reverse=True)
        self.sorted_names = [item[0] for item in roll_data]
        self.btn_start.setEnabled(True)
        self.btn_start.setStyleSheet(f"background-color: {CLR_ACCENT}; color: black;")

class PlayerSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yahtzee Setup")
        self.setFixedSize(400, 500)
        self.player_inputs = [] 
        layout = QVBoxLayout(self)
        header = QLabel("Player Registration")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold)); header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget(); self.input_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget); self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        self.add_player_slot()
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add Player"); add_btn.clicked.connect(self.add_player_slot)
        rem_btn = QPushButton("- Remove Player"); rem_btn.clicked.connect(self.remove_player_slot)
        btn_layout.addWidget(add_btn); btn_layout.addWidget(rem_btn); layout.addLayout(btn_layout)
        self.next_btn = QPushButton("Next: Determine Order")
        self.next_btn.setStyleSheet(f"background-color: {CLR_ACCENT}; color: black;")
        self.next_btn.clicked.connect(self.accept); layout.addWidget(self.next_btn)

    def add_player_slot(self):
        if len(self.player_inputs) < 8:
            row_widget = QWidget(); row_layout = QHBoxLayout(row_widget)
            inp = QLineEdit(); inp.setPlaceholderText(f"Player {len(self.player_inputs) + 1}")
            row_layout.addWidget(inp); self.input_layout.addWidget(row_widget)
            self.player_inputs.append((row_widget, inp))

    def remove_player_slot(self):
        if len(self.player_inputs) > 1:
            row_widget, _ = self.player_inputs.pop(); row_widget.deleteLater()

class YahtzeeScorecard(QMainWindow):
    def __init__(self, players):
        super().__init__()
        self.players = players
        self.current_turn_index = 0
        self.setWindowTitle("Yahtzee! Pro Scorecard")
        self.resize(1100, 900)
        
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.turn_label = QLabel(f"Current Turn: {self.players[0]}")
        self.turn_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.turn_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding: 10px;"); self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.turn_label)

        self.table = QTableWidget(len(ROW_LABELS), len(players))
        self.table.setVerticalHeaderLabels(ROW_LABELS); self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setup_table_cells()
        self.table.itemChanged.connect(self.handle_item_change)
        main_layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Export Results"); save_btn.clicked.connect(self.export_results)
        reset_btn = QPushButton("🔄 Reset Game"); reset_btn.setStyleSheet("background-color: #CF6679; color: black;"); reset_btn.clicked.connect(self.reset_game)
        btn_row.addWidget(save_btn); btn_row.addWidget(reset_btn); main_layout.addLayout(btn_row)
        
        self.update_turn_highlight()

    def setup_table_cells(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = QTableWidgetItem("-")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if row in CALCULATED_ROWS:
                    item.setText("0")
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(QColor(CLR_TOTAL_BG)); item.setForeground(QBrush(QColor(CLR_ACCENT)))
                    font = item.font(); font.setBold(True); item.setFont(font)
                
                elif 0 <= row <= 5: # Upper Section
                    self.create_combo(row, col, ["-", "0", "1", "2", "3", "4", "5"])
                
                elif row in FIXED_SCORE_VALUES: # Fixed Logic (Small Straight, etc.)
                    self.create_combo(row, col, ["-", "✓", "0"])
                
                else: # Manual entry rows (3 of kind, 4 of kind, chance, etc.)
                    item.setBackground(QColor(CLR_UNCLAIMED))
                
                self.table.setItem(row, col, item)

    def create_combo(self, row, col, items):
        combo = QComboBox()
        combo.addItems(items)
        combo.setProperty("row", row); combo.setProperty("col", col)
        combo.currentIndexChanged.connect(self.handle_combo_change)
        self.table.setCellWidget(row, col, combo)

    def handle_combo_change(self, index):
        combo = self.sender()
        row, col = combo.property("row"), combo.property("col")
        text = combo.currentText()
        
        self.table.blockSignals(True)
        item = self.table.item(row, col)
        was_unclaimed = item.text() == "-"
        
        if text == "-":
            item.setText("-")
            combo.setStyleSheet(f"background-color: {CLR_UNCLAIMED}; color: white;")
        else:
            # Determine score
            if row <= 5: # Upper
                score = int(text) * (row + 1)
            elif row in FIXED_SCORE_VALUES: # Fixed
                score = FIXED_SCORE_VALUES[row] if text == "✓" else 0
            
            item.setText(str(score))
            combo.setStyleSheet(f"background-color: {CLR_TABLE}; color: {CLR_CLAIMED_TEXT}; font-weight: bold;")
            if was_unclaimed: self.advance_turn(col)
        
        self.calculate_column(col); self.check_game_over()
        self.table.blockSignals(False)

    def handle_item_change(self, item):
        self.table.blockSignals(True)
        row, col = item.row(), item.column()
        if row not in CALCULATED_ROWS and self.table.cellWidget(row, col) is None:
            text = item.text()
            was_unclaimed = item.background().color().name().upper() == CLR_UNCLAIMED
            
            if text == "-":
                item.setBackground(QColor(CLR_UNCLAIMED))
            else:
                try:
                    val = int(text)
                    item.setBackground(QColor(CLR_TABLE)); item.setForeground(QBrush(QColor(CLR_CLAIMED_TEXT)))
                    if was_unclaimed: self.advance_turn(col)
                except ValueError: item.setText("-")
        
        self.calculate_column(col); self.check_game_over()
        self.table.blockSignals(False)

    def advance_turn(self, cell_col):
        if cell_col == self.current_turn_index:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            self.update_turn_highlight()

    def update_turn_highlight(self):
        self.turn_label.setText(f"Current Turn: {self.players[self.current_turn_index]}")
        for i in range(len(self.players)):
            header = QTableWidgetItem(f"▶ {self.players[i]}" if i == self.current_turn_index else self.players[i])
            header.setForeground(QBrush(QColor(CLR_ACTIVE_TURN if i == self.current_turn_index else CLR_CLAIMED_TEXT)))
            self.table.setHorizontalHeaderItem(i, header)

    def calculate_column(self, col):
        u_sum = sum(self.get_val(r, col) for r in range(6))
        bonus = 35 if u_sum >= 63 else 0
        self.table.item(6, col).setText(str(u_sum))
        self.table.item(7, col).setText(str(bonus))
        self.table.item(8, col).setText(str(u_sum + bonus))
        l_sum = sum(self.get_val(r, col) for r in [9,10,11,12,13,14,16]) + (self.get_val(15, col) * 100)
        self.table.item(17, col).setText(str(l_sum))
        self.table.item(18, col).setText(str(u_sum + bonus + l_sum))

    def get_val(self, r, c):
        item = self.table.item(r, c)
        return int(item.text()) if item and item.text().isdigit() else 0

    def check_game_over(self):
        for col in range(self.table.columnCount()):
            for row in INPUT_ROWS:
                if self.table.item(row, col).text() == "-": return 
        results = sorted([(self.players[c], self.get_val(18, c)) for c in range(self.table.columnCount())], key=lambda x: x[1], reverse=True)
        QMessageBox.information(self, "🏆 Victory!", f"Winner: {results[0][0]} with {results[0][1]} pts!")

    def export_results(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Scorecard", "yahtzee.txt", "Text Files (*.txt)")
        if path:
            with open(path, 'w') as f:
                f.write("YAHTZEE SCORECARD\n" + "="*30 + "\n")
                for r in range(len(ROW_LABELS)):
                    f.write(f"{ROW_LABELS[r]:<20} " + " ".join([f"{self.table.item(r, c).text():>5}" for c in range(len(self.players))]) + "\n")

    def reset_game(self):
        if QMessageBox.question(self, "Confirm", "Start over?") == QMessageBox.StandardButton.Yes:
            self.current_turn_index = 0; self.table.blockSignals(True)
            self.setup_table_cells(); self.update_turn_highlight(); self.table.blockSignals(False)

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyleSheet(DARK_STYLESHEET)
    setup = PlayerSetupDialog()
    if setup.exec():
        raw = [i.text().strip() or f"P{idx+1}" for idx, (_, i) in enumerate(setup.player_inputs)]
        rolloff = RollOffDialog(raw)
        if rolloff.exec():
            window = YahtzeeScorecard(rolloff.sorted_names); window.show(); sys.exit(app.exec())
