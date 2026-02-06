#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                             QScrollArea, QHeaderView, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QBrush

# --- Theme Configuration ---
CLR_BACKGROUND = "#121212"
CLR_TABLE = "#1E1E1E"
CLR_UNCLAIMED = "#2A2A2A"
CLR_ERROR = "#660000"
CLR_TOTAL_BG = "#000000"
CLR_ACCENT = "#03DAC6"     # Teal
CLR_CLAIMED_TEXT = "#BB86FC" # Purple

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
    QLineEdit {{ 
        background-color: #2D2D2D; 
        color: white; 
        border: 1px solid #3D3D3D; 
        border-radius: 4px;
        padding: 5px; 
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

UPPER_SECTION = ["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"]
LOWER_SECTION = ["3 of a Kind", "4 of a Kind", "Full House", "Small Straight", 
                 "Large Straight", "Yahtzee", "Yahtzee Bonus (Count)", "Chance"]
ROW_LABELS = (UPPER_SECTION + ["Sum", "Bonus (35)", "Total Upper"] + 
              LOWER_SECTION + ["Total Lower", "GRAND TOTAL"])

FIXED_SCORE_ROWS = {11: 25, 12: 30, 13: 40, 14: 50}
BONUS_YAHTZEE_ROW = 15
CALCULATED_ROWS = [6, 7, 8, 17, 18]
INPUT_ROWS = [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16]

class PlayerSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yahtzee Setup")
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
        add_btn = QPushButton("+ Add Player"); add_btn.clicked.connect(self.add_player_slot)
        rem_btn = QPushButton("- Remove Player"); rem_btn.clicked.connect(self.remove_player_slot)
        btn_layout.addWidget(add_btn); btn_layout.addWidget(rem_btn)
        layout.addLayout(btn_layout)
        
        start_btn = QPushButton("Start Game")
        start_btn.setStyleSheet(f"background-color: {CLR_ACCENT}; color: black;")
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)

    def add_player_slot(self):
        if len(self.player_inputs) < 8:
            row_widget = QWidget(); row_layout = QHBoxLayout(row_widget)
            lbl = QLabel(f"Player {len(self.player_inputs) + 1}:"); lbl.setFixedWidth(60)
            inp = QLineEdit()
            row_layout.addWidget(lbl); row_layout.addWidget(inp)
            self.input_layout.addWidget(row_widget)
            self.player_inputs.append((row_widget, inp))

    def remove_player_slot(self):
        if len(self.player_inputs) > 1:
            row_widget, _ = self.player_inputs.pop()
            row_widget.deleteLater()

class YahtzeeScorecard(QMainWindow):
    def __init__(self, players):
        super().__init__()
        self.players = players
        self.setWindowTitle("Yahtzee!")
        self.resize(1000, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.table = QTableWidget(len(ROW_LABELS), len(players))
        self.table.setVerticalHeaderLabels(ROW_LABELS)
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setup_table_cells()
        self.table.itemChanged.connect(self.handle_item_change)
        main_layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Export Results (TXT)"); save_btn.clicked.connect(self.export_results)
        reset_btn = QPushButton("🔄 Reset Game"); reset_btn.setStyleSheet("background-color: #CF6679; color: black;"); reset_btn.clicked.connect(self.reset_game)
        btn_row.addWidget(save_btn); btn_row.addWidget(reset_btn)
        main_layout.addLayout(btn_row)

    def setup_table_cells(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                if row in CALCULATED_ROWS:
                    item = QTableWidgetItem("0")
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(QColor(CLR_TOTAL_BG))
                    item.setForeground(QBrush(QColor(CLR_ACCENT)))
                    font = item.font(); font.setBold(True); item.setFont(font)
                    self.table.setItem(row, col, item)
                
                elif 0 <= row <= 5: # Upper Section Dropdowns
                    combo = QComboBox()
                    combo.addItems(["-", "0", "1", "2", "3", "4", "5"])
                    combo.setProperty("row", row)
                    combo.setProperty("col", col)
                    combo.currentIndexChanged.connect(self.handle_combo_change)
                    self.table.setCellWidget(row, col, combo)
                    # Invisible item for value tracking
                    item = QTableWidgetItem("-")
                    self.table.setItem(row, col, item)

                else: # Lower Section
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QColor(CLR_UNCLAIMED))
                    if row in FIXED_SCORE_ROWS:
                        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                        item.setCheckState(Qt.CheckState.Unchecked)
                    self.table.setItem(row, col, item)

    def handle_combo_change(self, index):
        combo = self.sender()
        row = combo.property("row")
        col = combo.property("col")
        text = combo.currentText()
        
        self.table.blockSignals(True)
        item = self.table.item(row, col)
        if text == "-":
            item.setText("-")
            combo.setStyleSheet(f"background-color: {CLR_UNCLAIMED}; color: white;")
        else:
            score = int(text) * (row + 1)
            item.setText(str(score))
            combo.setStyleSheet(f"background-color: {CLR_TABLE}; color: {CLR_CLAIMED_TEXT}; font-weight: bold;")
        
        self.calculate_column(col)
        self.check_game_over()
        self.table.blockSignals(False)

    def handle_item_change(self, item):
        self.table.blockSignals(True)
        row, col = item.row(), item.column()

        if row in FIXED_SCORE_ROWS:
            item.setText(str(FIXED_SCORE_ROWS[row]) if item.checkState() == Qt.CheckState.Checked else "-")

        text = item.text()
        if row not in CALCULATED_ROWS and not (0 <= row <= 5):
            if text == "-":
                item.setBackground(QColor(CLR_UNCLAIMED))
                item.setForeground(QBrush(QColor("#E0E0E0")))
            else:
                try:
                    val = int(text)
                    valid, msg = self.validate_score(row, val)
                    item.setBackground(QColor(CLR_ERROR if not valid else CLR_TABLE))
                    item.setForeground(QBrush(QColor(CLR_CLAIMED_TEXT if valid else "#FFFFFF")))
                    if not valid: item.setToolTip(msg)
                except ValueError:
                    item.setText("-")

        self.calculate_column(col)
        self.check_game_over()
        self.table.blockSignals(False)

    def validate_score(self, row, val):
        if val == 0: return True, ""
        if row in [9, 10, 16]:
            if val < 0 or val > 30: return False, "Range is 0-30"
        return True, ""

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
        item = self.table.item(r, c)
        if not item: return 0
        txt = item.text()
        return int(txt) if txt.isdigit() else 0

    def check_game_over(self):
        for col in range(self.table.columnCount()):
            for row in INPUT_ROWS:
                if self.table.item(row, col).text() == "-": return 
        self.show_winner_popup()

    def show_winner_popup(self):
        results = sorted([(self.players[c], self.get_val(18, c)) for c in range(self.table.columnCount())], key=lambda x: x[1], reverse=True)
        QMessageBox.information(self, "🏆 Victory!", f"Winner: {results[0][0]} with {results[0][1]} pts!")

    def export_results(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Scorecard", "yahtzee.txt", "Text Files (*.txt)")
        if path:
            with open(path, 'w') as f:
                f.write("YAHTZEE SCORECARD\n" + "="*30 + "\n")
                for r in range(len(ROW_LABELS)):
                    f.write(f"{ROW_LABELS[r]:<20} " + " ".join([f"{self.table.item(r, c).text():>5}" for c in range(len(self.players))]) + "\n")
            QMessageBox.information(self, "Success", "Saved!")

    def reset_game(self):
        if QMessageBox.question(self, "Confirm", "Start over?") == QMessageBox.StandardButton.Yes:
            self.table.blockSignals(True)
            self.setup_table_cells()
            self.table.blockSignals(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    setup = PlayerSetupDialog()
    if setup.exec():
        p_names = [i.text().strip() or f"P{idx+1}" for idx, (_, i) in enumerate(setup.player_inputs)]
        window = YahtzeeScorecard(p_names)
        window.show()
        sys.exit(app.exec())
