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
FIXED_SCORE_ROWS = {11: 25, 12: 30, 13: 40, 14: 50}
MANUAL_INPUT_ROWS = [9, 10, 16] 
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
        layout.addWidget(self.table)
        btns = QHBoxLayout()
        export, reset = QPushButton("Export Results"), QPushButton("Reset Game")
        export.clicked.connect(self.export_txt); reset.clicked.connect(self.reset)
        btns.addWidget(export); btns.addWidget(reset)
        layout.addLayout(btns)
        self.update_turn_ui()
    
    def advance_to_next_player(self):
        start_index = self.current_turn_index
        total_players = len(self.players)

        for _ in range(total_players):
            self.current_turn_index = (self.current_turn_index + 1) % total_players

            if self.player_has_turns_left(self.current_turn_index):
                self.update_turn_ui()
                return
            else:
                self.blink_column(self.current_turn_index, CLR_INVALID)

        # If we exit the loop, no players have turns left
        self.check_game_over()

    def player_has_turns_left(self, c):
        """
        A player has turns left if they have any non-bonus
        primary category unclaimed.

        Yahtzee Bonus does NOT count as a playable turn
        for skip logic purposes.
        """

        # Check all primary categories except Yahtzee Bonus
        for r in PRIMARY_CATEGORIES:
            if r == 15:
                continue

            if self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "unclaimed":
                return True

        # If we reach here, no normal categories remain.
        # Even if bonus is available, player is considered done.
        return False
    
    def blink_column(self, c, color):
        count = 0

        def toggle():
            nonlocal count
            for r in range(self.table.rowCount()):
                item = self.table.item(r, c)
                if item:
                    current = color if count % 2 == 0 else CLR_TABLE
                    item.setBackground(QColor(current))

            count += 1
            if count < 6:
                QTimer.singleShot(150, toggle)
            else:
                self.update_turn_ui()

        toggle()
    
    def update_yahtzee_bonus_state(self, c):
        yahtzee_item = self.table.item(14, c)
        bonus_widget = self.table.cellWidget(15, c)
        bonus_item = self.table.item(15, c)

        if not bonus_widget:
            return

        # Condition 1: Yahtzee must be claimed and > 0
        yahtzee_claimed = (
            yahtzee_item.data(Qt.ItemDataRole.UserRole) == "claimed"
            and yahtzee_item.text().isdigit()
            and int(yahtzee_item.text()) > 0
        )

        # Condition 2: Bonus cannot be the only unclaimed primary category
        unclaimed_primary = [
            r for r in PRIMARY_CATEGORIES
            if self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "unclaimed"
        ]

        bonus_is_only_remaining = (unclaimed_primary == [15])

        enable_bonus = yahtzee_claimed and not bonus_is_only_remaining

        bonus_widget.setEnabled(enable_bonus)

        if not enable_bonus and bonus_item.data(Qt.ItemDataRole.UserRole) == "unclaimed":
            bonus_widget.setStyleSheet("background-color: #151515; color: #555555;")

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
                    self.add_dropdown(r, c, ["-", "1", "2", "3", "4", "5"])
                elif r == 15:
                    self.add_dropdown(r, c, ["-", "1", "2", "3", "4", "5"])
                elif r in FIXED_SCORE_ROWS:
                    self.add_dropdown(r, c, ["-", "✓", "0"])
                elif r in MANUAL_INPUT_ROWS:
                    self.add_manual_input(r, c)
                else:
                    item.setBackground(QColor(CLR_UNCLAIMED))
                self.table.setItem(r, c, item)
        self.table.blockSignals(False)
        for c in range(self.table.columnCount()):
            self.update_yahtzee_bonus_state(c)


    def add_dropdown(self, r, c, options):
        combo = QComboBox()
        combo.addItems(options)
        combo.setProperty("row", r); combo.setProperty("col", c)
        combo.currentIndexChanged.connect(self.handle_dropdown)
        self.table.setCellWidget(r, c, combo)

    def add_manual_input(self, r, c):
        edit = QLineEdit()
        edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit.setProperty("row", r); edit.setProperty("col", c)
        edit.editingFinished.connect(self.handle_manual_entry)
        self.table.setCellWidget(r, c, edit)

    def blink_cell(self, r, c, color):
        """Safely blinks a cell, handling potential deletion of C++ objects."""
        widget = self.table.cellWidget(r, c)
        item = self.table.item(r, c)
        if not item: return

        # Capture state before turn might advance
        is_claimed = item.data(Qt.ItemDataRole.UserRole) == "claimed"
        target_bg = CLR_TABLE if is_claimed else (CLR_ACTIVE_UNCLAIMED if c == self.current_turn_index else CLR_UNCLAIMED)
        text_clr = CLR_CLAIMED_TEXT if is_claimed else "white"

        count = 0
        def toggle():
            nonlocal count
            try:
                # Security check: Does widget/item still belong to this cell?
                if self.table.cellWidget(r, c) is not widget or self.table.item(r, c) is not item:
                    return

                current_color = color if count % 2 == 0 else target_bg
                if widget:
                    widget.setStyleSheet(f"background-color: {current_color}; color: {text_clr}; border: none;")
                item.setBackground(QColor(current_color))
                
                count += 1
                if count < 8:
                    QTimer.singleShot(150, toggle)
                else:
                    self.update_turn_ui()
            except RuntimeError:
                pass # Widget was deleted (e.g. game reset)

        toggle()

    def handle_dropdown(self, index):
        if self._is_updating:
            return

        combo = self.sender()
        r = combo.property("row")
        c = combo.property("col")
        text = combo.currentText()

        if text == "-":
            return

        if c != self.current_turn_index:
            if QMessageBox.question(
                self,
                "Confirm Entry",
                f"It is {self.players[self.current_turn_index]}'s turn. Edit {self.players[c]} anyway?"
            ) == QMessageBox.StandardButton.No:
                self.table.blockSignals(True)
                combo.setCurrentIndex(0)
                self.table.blockSignals(False)
                return

        self._is_updating = True
        item = self.table.item(r, c)

        previous_text = item.text()
        previous_score = int(previous_text) if previous_text.isdigit() else 0
        was_unclaimed = item.data(Qt.ItemDataRole.UserRole) == "unclaimed"

        # ----- Score Calculation -----
        if r in UPPER_SECTION:
            score = int(text) * (r + 1)
        elif r in FIXED_SCORE_ROWS:
            score = FIXED_SCORE_ROWS[r] if text == "✓" else 0
        elif r == 15:
            score = int(text) * 100
        else:
            score = 0

        item.setText(str(score))
        item.setData(Qt.ItemDataRole.UserRole, "claimed")

        # ----- Turn Advancement Logic -----
        advance_turn = False

        if r == 15:
            # Advance only if bonus count increased
            new_count = int(text)
            previous_count = previous_score // 100 if previous_score else 0
            if new_count > previous_count and c == self.current_turn_index:
                advance_turn = True
        else:
            if was_unclaimed and c == self.current_turn_index:
                advance_turn = True

        self.recalc(c)
        self.blink_cell(r, c, CLR_VALID)

        if advance_turn:
            self.current_turn_index = (
                self.current_turn_index + 1
            ) % len(self.players)

        self._is_updating = False
        self.update_yahtzee_bonus_state(c)

    def handle_manual_entry(self):
        if self._is_updating: return
        edit = self.sender()
        r, c, text = edit.property("row"), edit.property("col"), edit.text()
        if not text or text == "-": return

        if c != self.current_turn_index:
            if QMessageBox.question(self, 'Confirm Entry', f"It is {self.players[self.current_turn_index]}'s turn. Edit {self.players[c]} anyway?") == QMessageBox.StandardButton.No:
                edit.setText(""); return

        self._is_updating = True
        try:
            val = int(text)
            valid = (0 <= val <= 30) if r in [9, 10, 16] else (0 <= val <= 12 if r == 15 else False)
            if valid:
                item = self.table.item(r, c)
                is_new = item.data(Qt.ItemDataRole.UserRole) == "unclaimed"
                item.setText(str(val)); item.setData(Qt.ItemDataRole.UserRole, "claimed")
                self.recalc(c); self.blink_cell(r, c, CLR_VALID)
                if is_new and r != 15 and c == self.current_turn_index:
                    self.advance_to_next_player()
            else:
                self.blink_cell(r, c, CLR_INVALID)
                QMessageBox.warning(self, "Invalid Score", f"'{val}' is impossible for this category.")
                edit.setText("")
        except ValueError:
            edit.setText("")
        self._is_updating = False
        self.update_yahtzee_bonus_state(c)

    def update_turn_ui(self):
        self.turn_label.setText(f"Active Turn: {self.players[self.current_turn_index]}")
        for c in range(self.table.columnCount()):
            is_active = (c == self.current_turn_index)
            h_item = QTableWidgetItem(f"▶ {self.players[c]}" if is_active else self.players[c])
            h_item.setForeground(QBrush(QColor(CLR_ACTIVE_TURN if is_active else "#555555")))
            self.table.setHorizontalHeaderItem(c, h_item)
            for r in range(self.table.rowCount()):
                if r in CALCULATED_ROWS: continue
                item, widget = self.table.item(r, c), self.table.cellWidget(r, c)
                status = item.data(Qt.ItemDataRole.UserRole)
                bg = CLR_TABLE if status == "claimed" else (CLR_ACTIVE_UNCLAIMED if is_active else CLR_UNCLAIMED)
                item.setBackground(QColor(bg))
                if widget:
                    txt_clr = CLR_CLAIMED_TEXT if status == "claimed" else "white"
                    fw = "bold" if status == "claimed" else "normal"
                    widget.setStyleSheet(f"background-color: {bg}; color: {txt_clr}; font-weight: {fw}; border: none;")

    def recalc(self, c):
        u_sum = sum(int(self.table.item(r, c).text()) for r in range(6) if self.table.item(r, c).text().isdigit())
        self.table.item(6, c).setText(str(u_sum))
        bonus = 35 if u_sum >= 63 else 0
        self.table.item(7, c).setText(str(bonus))
        self.table.item(8, c).setText(str(u_sum + bonus))
        l_sum = sum(int(self.table.item(r, c).text()) for r in [9, 10, 11, 12, 13, 14, 16] if self.table.item(r, c).text().isdigit())
        y_bonus = int(self.table.item(15, c).text()) if self.table.item(15, c).text().isdigit() else 0
        self.table.item(17, c).setText(str(l_sum + y_bonus))
        self.table.item(18, c).setText(str(u_sum + bonus + l_sum + y_bonus))
        self.check_game_over()

    def check_game_over(self):
        for c in range(self.table.columnCount()):
            for r in PRIMARY_CATEGORIES:
                if self.table.item(r, c).text() == "-": return
        scores = sorted([(self.players[i], int(self.table.item(18, i).text())) for i in range(len(self.players))], key=lambda x: x[1], reverse=True)
        msg = QMessageBox(self)
        msg.setWindowTitle("Game Over"); msg.setText(f"🏆 Winner: {scores[0][0]} ({scores[0][1]} pts)")
        btn_play = msg.addButton("Play Again", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Exit", QMessageBox.ButtonRole.RejectRole); msg.exec()
        if msg.clickedButton() == btn_play:
            self.play_again_requested = True
        self.close()

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Scorecard", "", "Text Files (*.txt)")
        if path:
            with open(path, 'w') as f:
                for r in range(len(ROW_LABELS)):
                    f.write(f"{ROW_LABELS[r]:<20} | {' | '.join([self.table.item(r, c).text() for c in range(len(self.players))])}\n")

    def reset(self):
        if QMessageBox.question(self, "Reset", "Clear scores?") == QMessageBox.StandardButton.Yes:
            self.current_turn_index = 0; self.setup_board(); self.update_turn_ui()

    def closeEvent(self, event):
        if hasattr(self, 'loop'):
            self.loop.quit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyleSheet(DARK_STYLESHEET)
    setup = PlayerSetupDialog()
    if setup.exec():
        names = [i.text().strip() or f"P{idx+1}" for idx, (_, i) in enumerate(setup.player_inputs)]
        while True:
            rolloff = RollOffDialog(names)
            if rolloff.exec() == QDialog.DialogCode.Accepted:
                w = YahtzeeScorecard(rolloff.sorted_names)
                w.loop = QEventLoop()  # Attach loop to window
                w.show()
                w.loop.exec()          # Wait for closeEvent to call loop.quit()
                
                if not getattr(w, 'play_again_requested', False): 
                    break
            else: 
                break
