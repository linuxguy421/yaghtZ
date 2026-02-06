#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                             QScrollArea, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QBrush, QPalette

# --- Styling & Constants ---
DARK_STYLESHEET = """
    QMainWindow, QDialog, QWidget {
        background-color: #121212;
        color: #E0E0E0;
    }
    QTableWidget {
        background-color: #1E1E1E;
        color: #E0E0E0;
        gridline-color: #333333;
        border: 1px solid #333333;
        font-size: 13px;
    }
    QHeaderView::section {
        background-color: #252525;
        color: #BB86FC;
        padding: 5px;
        border: 1px solid #333333;
        font-weight: bold;
    }
    QLineEdit {
        background-color: #2D2D2D;
        color: white;
        border: 1px solid #3D3D3D;
        border-radius: 4px;
        padding: 5px;
    }
    QPushButton {
        background-color: #333333;
        color: white;
        border-radius: 4px;
        padding: 8px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #444444;
    }
    QScrollArea {
        border: none;
    }
"""

UPPER_SECTION = ["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"]
LOWER_SECTION = ["3 of a Kind", "4 of a Kind", "Full House", "Small Straight", 
                 "Large Straight", "Yahtzee", "Yahtzee Bonus (Count)", "Chance"]

ROW_LABELS = (UPPER_SECTION + ["Sum", "Bonus (35)", "Total Upper"] + 
              LOWER_SECTION + ["Total Lower", "GRAND TOTAL"])

FIXED_SCORE_ROWS = {11: 25, 12: 30, 13: 40, 14: 50}
BONUS_YAHTZEE_ROW = 15
CALCULATED_ROWS = [6, 7, 8, 17, 18]

class PlayerSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yahtzee Setup")
        self.setFixedSize(400, 500)
        self.player_names = []
        
        layout = QVBoxLayout(self)
        lbl_instr = QLabel("Enter Player Names (1-8 Players):")
        lbl_instr.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_instr)
        
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.input_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.name_inputs = []
        self.add_player_slot()
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("+ Add Player")
        self.btn_add.clicked.connect(self.add_player_slot)
        self.btn_remove = QPushButton("- Remove Player")
        self.btn_remove.clicked.connect(self.remove_player_slot)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        layout.addLayout(btn_layout)
        
        self.btn_start = QPushButton("Start Scoring")
        self.btn_start.setStyleSheet("background-color: #03DAC6; color: black;")
        self.btn_start.clicked.connect(self.validate_and_start)
        layout.addWidget(self.btn_start)

    def add_player_slot(self):
        if len(self.name_inputs) < 8:
            lbl = QLabel(f"Player {len(self.name_inputs) + 1}:")
            inp = QLineEdit()
            self.input_layout.addWidget(lbl)
            self.input_layout.addWidget(inp)
            self.name_inputs.append((lbl, inp))

    def remove_player_slot(self):
        if len(self.name_inputs) > 1:
            lbl, inp = self.name_inputs.pop()
            lbl.deleteLater()
            inp.deleteLater()

    def validate_and_start(self):
        self.player_names = [inp.text().strip() or f"Player {i+1}" for i, (_, inp) in enumerate(self.name_inputs)]
        self.accept()

class YahtzeeScorecard(QMainWindow):
    def __init__(self, players):
        super().__init__()
        self.players = players
        self.setWindowTitle("Yahtzee! Dark Mode")
        self.resize(1000, 850)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.table = QTableWidget(len(ROW_LABELS), len(players))
        self.table.setVerticalHeaderLabels(ROW_LABELS)
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.setup_table_cells()
        self.table.itemChanged.connect(self.handle_item_change)
        layout.addWidget(self.table)

        btn_reset = QPushButton("Reset Game")
        btn_reset.setStyleSheet("background-color: #CF6679; color: black;")
        btn_reset.clicked.connect(self.reset_game)
        layout.addWidget(btn_reset)

    def setup_table_cells(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if row in CALCULATED_ROWS:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(QColor("#000000"))
                    item.setForeground(QBrush(QColor("#03DAC6"))) # Teal text for totals
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                elif row in FIXED_SCORE_ROWS:
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    item.setCheckState(Qt.CheckState.Unchecked)
                elif row == BONUS_YAHTZEE_ROW:
                    item.setBackground(QColor("#2C2C2C")) # Slightly different for bonus row
                
                self.table.setItem(row, col, item)

    def validate_score(self, row, val):
        if val == 0: return True, ""
        if 0 <= row <= 5:
            mult = row + 1
            if val % mult != 0 or val > (mult * 5):
                return False, f"Must be multiple of {mult} (max {mult*5})"
        if row in [9, 10, 16]:
            if val < 5 or val > 30:
                return False, "Score must be 5-30"
        return True, ""

    def handle_item_change(self, item):
        self.table.blockSignals(True)
        row, col = item.row(), item.column()

        if row in FIXED_SCORE_ROWS:
            item.setText(str(FIXED_SCORE_ROWS[row]) if item.checkState() == Qt.CheckState.Checked else "0")

        try:
            val = int(item.text())
            is_valid, msg = self.validate_score(row, val)
            
            if not is_valid and row not in CALCULATED_ROWS:
                item.setBackground(QColor("#660000")) # Deep Red for dark mode
                item.setToolTip(msg)
            else:
                if row not in CALCULATED_ROWS:
                    item.setBackground(QColor("#1E1E1E")) 
                    item.setToolTip("")
        except ValueError:
            item.setText("0")

        self.calculate_column(col)
        self.table.blockSignals(False)

    def calculate_column(self, col):
        u_sum = sum(self.get_val(r, col) for r in range(6))
        bonus = 35 if u_sum >= 63 else 0
        self.table.item(6, col).setText(str(u_sum))
        self.table.item(7, col).setText(str(bonus))
        self.table.item(8, col).setText(str(u_sum + bonus))

        l_sum = sum(self.get_val(r, col) for r in [9,10,11,12,13,14,16])
        l_sum += (self.get_val(BONUS_YAHTZEE_ROW, col) * 100)
        
        self.table.item(17, col).setText(str(l_sum))
        self.table.item(18, col).setText(str(u_sum + bonus + l_sum))

    def get_val(self, r, c):
        try: return int(self.table.item(r, c).text())
        except: return 0

    def reset_game(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if r in FIXED_SCORE_ROWS: item.setCheckState(Qt.CheckState.Unchecked)
                if r not in CALCULATED_ROWS: 
                    item.setText("0")
                    item.setBackground(QColor("#1E1E1E"))
        self.table.blockSignals(False)
        for c in range(self.table.columnCount()): self.calculate_column(c)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    
    setup = PlayerSetupDialog()
    if setup.exec():
        window = YahtzeeScorecard(setup.player_names)
        window.show()
        sys.exit(app.exec())