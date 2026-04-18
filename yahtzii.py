#!/usr/bin/env python3
"""
yahtzee.py — Pro Yahtzii Scorecard + Optional Digital Roller
Merged from yahtzee.py (scorecard) and roll.py (animated roller).

Requires: pip install PyQt6 PyQt6-Qt6 PyQt6-sip
Run:      python yahtzee.py
"""

import sys
import random
import time
import math
import json
import os
from datetime import datetime
from collections import Counter, defaultdict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QScrollArea, QHeaderView, QComboBox, QMenu,
    QTextEdit, QStatusBar, QCheckBox, QFrame, QProgressBar,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QEventLoop, QByteArray, QElapsedTimer, QRectF
from PyQt6.QtGui import (
    QColor, QFont, QBrush, QPainter, QPen, QPalette, QPixmap,
)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer

# ============================================================================
# THEME — Midnight Steel (scorecard)
# ============================================================================
CLR_BACKGROUND      = "#0F1117"
CLR_TABLE           = "#161B27"
CLR_UNCLAIMED       = "#1E2740"
CLR_ACTIVE_UNCLAIMED= "#253354"
CLR_TOTAL_BG        = "#0A0D14"
CLR_ACCENT          = "#3B82F6"
CLR_CLAIMED_TEXT    = "#93C5FD"
CLR_ACTIVE_TURN     = "#FBBF24"
CLR_DISABLED        = "#0D1020"
CLR_VALID           = "#34D399"
CLR_INVALID         = "#F87171"
CLR_ACCENT_HOVER    = "#2563EB"
CLR_PURPLE_HOVER    = "#1D4ED8"

def accent_btn_style():
    return (f"QPushButton {{ background-color: #3B82F6; color: black; border-radius: 4px; "
            f"padding: 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {CLR_ACCENT_HOVER}; }}")

def purple_btn_style():
    return (f"QPushButton {{ background-color: #93C5FD; color: black; border-radius: 4px; "
            f"padding: 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {CLR_PURPLE_HOVER}; }}")

DARK_STYLESHEET = f"""
    QMainWindow, QDialog, QWidget {{ background-color: {CLR_BACKGROUND}; color: #F1F5F9; }}
    QTableWidget {{ background-color: {CLR_TABLE}; color: #F1F5F9; gridline-color: #1A2540;
                    border: 1px solid #1A2540; }}
    QHeaderView::section {{ background-color: #1A2540; color: {CLR_CLAIMED_TEXT};
                             padding: 5px; border: 1px solid #2E3F60; font-weight: bold; }}
    QComboBox, QLineEdit {{ background-color: {CLR_UNCLAIMED}; color: #F1F5F9;
                            border: 1px solid #2E3F60; border-radius: 3px; padding: 2px; }}
    QComboBox::drop-down {{ border: none; background-color: {CLR_UNCLAIMED}; }}
    QComboBox::down-arrow {{ width: 10px; height: 10px; }}
    QComboBox QAbstractItemView {{
        background-color: {CLR_TABLE};
        color: #F1F5F9;
        border: 1px solid #2E3F60;
        selection-background-color: {CLR_ACCENT};
        selection-color: #000000;
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 4px 8px;
        min-height: 24px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background-color: {CLR_ACTIVE_UNCLAIMED};
        color: #F1F5F9;
    }}
    QPushButton {{ background-color: #1E2740; color: #F1F5F9; border-radius: 4px;
                   padding: 10px; font-weight: bold; }}
    QPushButton:hover {{ background-color: #253354; }}
    QCheckBox {{ color: #F1F5F9; }}
"""


# ============================================================================
# SCORE BUTTON  — QPushButton + QMenu replaces QComboBox for score cells.
# QMenu is fully styleable; QComboBox popups ignore stylesheets on Linux.
# ============================================================================
class ScoreButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._options   = []
        self._current   = "-"
        self._accent    = "#3B82F6"
        self._bg        = "#161B27"
        self._hover_bg  = "#253354"
        self._row       = -1
        self._col       = -1
        self._on_change = None
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._show_menu)

    def addItems(self, items):
        self._options = list(items)
        self._current = self._options[0] if self._options else "-"
        self._refresh_text()

    def clear(self):
        self._options = []
        self._current = "-"
        self._refresh_text()

    def currentText(self):
        return self._current

    def setCurrentIndex(self, idx):
        if 0 <= idx < len(self._options):
            self._current = self._options[idx]
            self._refresh_text()

    def findText(self, text):
        try:    return self._options.index(text)
        except: return -1

    def setProperty(self, name, value):
        if   name == "row": self._row = value
        elif name == "col": self._col = value
        else: super().setProperty(name, value)

    def property(self, name):
        if name == "row": return self._row
        if name == "col": return self._col
        return super().property(name)

    def connect_change(self, callback):
        self._on_change = callback

    def set_theme_colors(self, accent, bg, hover_bg):
        self._accent   = accent
        self._bg       = bg
        self._hover_bg = hover_bg

    def apply_cell_style(self, bg_color, text_color):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 1px 4px;
                text-align: left;
            }}
            QPushButton:hover {{ background-color: {self._hover_bg}; }}
        """)

    def _refresh_text(self):
        self.setText(f"{self._current}  ▾")

    def _show_menu(self):
        if not self._options or not self.isEnabled():
            return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self._bg};
                color: #F1F5F9;
                border: 1px solid {self._accent};
                padding: 2px;
            }}
            QMenu::item {{ padding: 4px 16px; min-width: 60px; }}
            QMenu::item:selected {{
                background-color: {self._accent};
                color: #000000;
            }}
        """)
        for opt in self._options:
            menu.addAction(opt).setData(opt)
        chosen = menu.exec(self.mapToGlobal(self.rect().bottomLeft()))
        if chosen is not None:
            new_text = chosen.data()
            old_idx  = self.findText(self._current)
            new_idx  = self.findText(new_text)
            self._current = new_text
            self._refresh_text()
            if self._on_change and new_idx != old_idx:
                self._on_change(new_idx, self)


# ============================================================================
# SCORECARD CONSTANTS
# ============================================================================
UPPER_SECTION        = [0, 1, 2, 3, 4, 5]
LOWER_SECTION_PRIMARY= [9, 10, 11, 12, 13, 16]
FIXED_SCORE_ROWS     = {11: 25, 12: 30, 13: 40, 14: 50}
CALCULATED_ROWS      = [6, 7, 8, 17, 18]
PRIMARY_CATEGORIES   = [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 16]

ROW_LABELS = (
    ["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"] +
    ["Sum", "Bonus (35)", "Total Upper"] +
    ["3 of a Kind", "4 of a Kind", "Full House", "Small Straight",
     "Large Straight", "Yahtzii", "Yahtzii Bonus (Count)", "Chance"] +
    ["Total Lower", "GRAND TOTAL"]
)

# ============================================================================
# ROLLER SVG DATA  (inline — no external files needed)
# ============================================================================
_ROLLER_SVG_PATHS = {
    1: "M15 1H1V15H15V1ZM8 9.5C8.82843 9.5 9.5 8.82843 9.5 8C9.5 7.17157 8.82843 6.5 8 6.5C7.17157 6.5 6.5 7.17157 6.5 8C6.5 8.82843 7.17157 9.5 8 9.5Z",
    2: "M1 1H15V15H1V1ZM7 5.5C7 6.32843 6.32843 7 5.5 7C4.67157 7 4 6.32843 4 5.5C4 4.67157 4.67157 4 5.5 4C6.32843 4 7 4.67157 7 5.5ZM10.5 12C11.3284 12 12 11.3284 12 10.5C12 9.67157 11.3284 9 10.5 9C9.67157 9 9 9.67157 9 10.5C9 11.3284 9.67157 12 10.5 12Z",
    3: "M15 1H1V15H15V1ZM4.5 6C5.32843 6 6 5.32843 6 4.5C6 3.67157 5.32843 3 4.5 3C3.67157 3 3 3.67157 3 4.5C3 5.32843 3.67157 6 4.5 6ZM9.5 8C9.5 8.82843 8.82843 9.5 8 9.5C7.17157 9.5 6.5 8.82843 6.5 8C6.5 7.17157 7.17157 6.5 8 6.5C8.82843 6.5 9.5 7.17157 9.5 8ZM11.5 13C12.3284 13 13 12.3284 13 11.5C13 10.6716 12.3284 10 11.5 10C10.6716 10 10 10.6716 10 11.5C10 12.3284 10.6716 13 11.5 13Z",
    4: "M1 1H15V15H1V1ZM6 4.5C6 5.32843 5.32843 6 4.5 6C3.67157 6 3 5.32843 3 4.5C3 3.67157 3.67157 3 4.5 3C5.32843 3 6 3.67157 6 4.5ZM11.5 6C12.3284 6 13 5.32843 13 4.5C13 3.67157 12.3284 3 11.5 3C10.6716 3 10 3.67157 10 4.5C10 5.32843 10.6716 6 11.5 6ZM6 11.5C6 12.3284 5.32843 13 4.5 13C3.67157 13 3 12.3284 3 11.5C3 10.6716 3.67157 10 4.5 10C5.32843 10 6 10.6716 6 11.5ZM11.5 13C12.3284 13 13 12.3284 13 11.5C13 10.6716 12.3284 10 11.5 10C10.6716 10 10 10.6716 10 11.5C10 12.3284 10.6716 13 11.5 13Z",
    5: "M15 1H1V15H15V1ZM4.5 6C5.32843 6 6 5.32843 6 4.5C6 3.67157 5.32843 3 4.5 3C3.67157 3 3 3.67157 3 4.5C3 5.32843 3.67157 6 4.5 6ZM13 4.5C13 5.32843 12.3284 6 11.5 6C10.6716 6 10 5.32843 10 4.5C10 3.67157 10.6716 3 11.5 3C12.3284 3 13 3.67157 13 4.5ZM8 9.5C8.82843 9.5 9.5 8.82843 9.5 8C9.5 7.17157 8.82843 6.5 8 6.5C7.17157 6.5 6.5 7.17157 6.5 8C6.5 8.82843 7.17157 9.5 8 9.5ZM6 11.5C6 12.3284 5.32843 13 4.5 13C3.67157 13 3 12.3284 3 11.5C3 10.6716 3.67157 10 4.5 10C5.32843 10 6 10.6716 6 11.5ZM11.5 13C12.3284 13 13 12.3284 13 11.5C13 10.6716 12.3284 10 11.5 10C10.6716 10 10 10.6716 10 11.5C10 12.3284 10.6716 13 11.5 13Z",
    6: "M1 1H15V15H1V1ZM6 4C6 4.82843 5.32843 5.5 4.5 5.5C3.67157 5.5 3 4.82843 3 4C3 3.17157 3.67157 2.5 4.5 2.5C5.32843 2.5 6 3.17157 6 4ZM11.5 5.5C12.3284 5.5 13 4.82843 13 4C13 3.17157 12.3284 2.5 11.5 2.5C10.6716 2.5 10 3.17157 10 4C10 4.82843 10.6716 5.5 11.5 5.5ZM6 12C6 12.8284 5.32843 13.5 4.5 13.5C3.67157 13.5 3 12.8284 3 12C3 11.1716 3.67157 10.5 4.5 10.5C5.32843 10.5 6 11.1716 6 12ZM11.5 13.5C12.3284 13.5 13 12.8284 13 12C13 11.1716 12.3284 10.5 11.5 10.5C10.6716 10.5 10 11.1716 10 12C10 12.8284 10.6716 13.5 11.5 13.5ZM6 8C6 8.82843 5.32843 9.5 4.5 9.5C3.67157 9.5 3 8.82843 3 8C3 7.17157 3.67157 6.5 4.5 6.5C5.32843 6.5 6 7.17157 6 8ZM11.5 9.5C12.3284 9.5 13 8.82843 13 8C13 7.17157 12.3284 6.5 11.5 6.5C10.6716 6.5 10 7.17157 10 8C10 8.82843 10.6716 9.5 11.5 9.5Z",
}

_ROLLER_THEMES = {
    "Classic": {"bg": "#1a1a2e", "accent": "#e94560", "bar_start": "#e94560", "bar_end": "#f5a623"},
    "Forest":  {"bg": "#1b2e1a", "accent": "#4ade80", "bar_start": "#4ade80", "bar_end": "#86efac"},
    "Ocean":   {"bg": "#0a1628", "accent": "#38bdf8", "bar_start": "#0ea5e9", "bar_end": "#38bdf8"},
    "Sunset":  {"bg": "#2d1b0e", "accent": "#fb923c", "bar_start": "#f97316", "bar_end": "#fbbf24"},
    "Storm":   {"bg": "#1a1a1a", "accent": "#a78bfa", "bar_start": "#7c3aed", "bar_end": "#a78bfa"},
    "Neon":    {"bg": "#0b0b0f", "accent": "#22d3ee", "bar_start": "#06b6d4", "bar_end": "#a21caf"},
    "Lava":    {"bg": "#220a0a", "accent": "#ef4444", "bar_start": "#dc2626", "bar_end": "#f97316"},
    "Lemon":    {"bg": "#1f1700", "accent": "#facc15", "bar_start": "#eab308", "bar_end": "#fde047"},
    "Arctic":  {"bg": "#0b1b24", "accent": "#67e8f9", "bar_start": "#0891b2", "bar_end": "#cffafe"},
    "Cyber":   {"bg": "#12091f", "accent": "#c084fc", "bar_start": "#9333ea", "bar_end": "#ec4899"},
}

def _make_roller_svg(face: int, dot_color: str = "#ffffff") -> bytes:
    path = _ROLLER_SVG_PATHS[face]
    svg = (f'<svg width="80" height="80" viewBox="0 0 16 16" fill="none" '
           f'xmlns="http://www.w3.org/2000/svg">'
           f'<path fill-rule="evenodd" clip-rule="evenodd" d="{path}" fill="{dot_color}"/>'
           f'</svg>')
    return svg.encode()


def _load_die_svg(face: int, color: str) -> bytes:
    """Load images/{face}.svg if present, else fall back to inline SVG."""
    path = os.path.join("images", f"{face}.svg")
    try:
        with open(path, "r", encoding="utf-8") as f:
            svg = f.read()
        svg = svg.replace('fill="#000000"', f'fill="{color}"')
        svg = svg.replace("fill='#000000'", f"fill='{color}'")
        return svg.encode("utf-8")
    except FileNotFoundError:
        return _make_roller_svg(face, color)


# ============================================================================
# ROLLER — DieWidget
# ============================================================================
class DieWidget(QWidget):
    SIZE = 80

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index    = index
        self.face     = 1
        self.held     = False
        self.rolling  = False
        self.blank    = False

        # Animation state driven by the roller each frame
        self.anim_t        = 0.0
        self.anim_settled  = False

        # 3-D flip state
        self.spin_angle    = 0.0    # cumulative Y-rotation degrees
        self.snap_target   = 0.0    # nearest 360° multiple to snap to on settle
        self.snap_t        = -1.0   # -1 = no snap; 0→1 = snap progress
        self.SNAP_DUR      = 80     # ms for the snap-to-upright tween
        self.visual_face   = 1

        # Landing bounce: -1 = not yet; 0→1 = progress
        self.land_t        = -1.0
        self.land_start    = 0.0    # per-die timestamp (not shared)
        self.LAND_DUR      = 260    # ms

        # Held idle pulse
        self.pulse_t       = 0.0    # driven by the roller's idle timer

        self.setFixedSize(self.SIZE + 12, self.SIZE + 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.held_label = QLabel("HELD", self)
        self.held_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.held_label.setFixedWidth(self.SIZE + 12)
        self.held_label.move(0, self.SIZE + 10)
        self.held_label.setStyleSheet(
            "color: #fbbf24; font-size: 9px; font-weight: bold; letter-spacing: 2px;"
        )
        self.held_label.hide()

    # ---------------------------------------------------------------- SVG ----
    def _svg_bytes(self, face: int, dot_color: str = "#ffffff") -> bytes:
        if self.blank:
            return (
                b'<svg width="80" height="80" viewBox="0 0 16 16" fill="none" '
                b'xmlns="http://www.w3.org/2000/svg">'
                b'<rect x="1" y="1" width="14" height="14" rx="1.5" '
                b'fill="none" stroke="#ffffff22" stroke-width="0.75"/>'
                b'</svg>'
            )
        path = _ROLLER_SVG_PATHS[face]
        svg = (f'<svg width="80" height="80" viewBox="0 0 16 16" fill="none" '
               f'xmlns="http://www.w3.org/2000/svg">'
               f'<path fill-rule="evenodd" clip-rule="evenodd" '
               f'd="{path}" fill="{dot_color}"/>'
               f'</svg>')
        return svg.encode()

    def _render_face(self, face: int, dot_color: str) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(self._svg_bytes(face, dot_color)))
        pix = QPixmap(self.SIZE, self.SIZE)
        pix.fill(Qt.GlobalColor.transparent)
        pp = QPainter(pix)
        pp.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(pp)
        pp.end()
        return pix

    # ---------------------------------------------------------------- paint --
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        W      = self.SIZE + 12
        cx     = W / 2
        die_cy = (self.SIZE + 6) / 2

        # ── Accent colour ─────────────────────────────────────────────────
        accent_hex = "#ffffff"
        accent_rgb = (255, 255, 255)
        if self.held:
            try:
                h = _ROLLER_THEMES[self.parent().current_theme]["accent"].lstrip("#")
                accent_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                accent_hex = _ROLLER_THEMES[self.parent().current_theme]["accent"]
            except Exception:
                accent_hex = "#fbbf24"
                accent_rgb = (251, 191, 36)

        # ── Effective spin angle (snap tween overrides at end of roll) ────
        if 0.0 <= self.snap_t < 1.0:
            st = self.snap_t
            ease_snap = 1.0 - (1.0 - st) ** 3
            display_angle = self.spin_angle + (self.snap_target - self.spin_angle) * ease_snap
        else:
            display_angle = self.spin_angle

        angle_mod    = display_angle % 360
        x_scale      = abs(math.cos(math.radians(angle_mod)))
        show_front   = (angle_mod < 90 or angle_mod >= 270)
        display_face = self.visual_face if show_front else self.face

        # ── Per-state values ──────────────────────────────────────────────
        y_squash     = 1.0
        y_offset     = 0.0
        shadow_alpha = 40
        opacity      = 1.0
        glow_alpha   = 0

        if self.rolling and not self.anim_settled:
            rock         = math.sin(math.radians(self.spin_angle * 0.6)) * 0.05
            y_squash     = 1.0 + rock
            shadow_alpha = int(25 + 55 * x_scale)
            opacity      = min(1.0, 0.3 + self.anim_t * 2.5)

        elif 0.0 <= self.land_t < 1.0:
            lt = self.land_t
            if lt < 0.20:
                y_squash = 1.0 - (lt / 0.20) * 0.28
            elif lt < 0.55:
                st       = (lt - 0.20) / 0.35
                y_squash = 0.72 + st * 0.40        # 0.72 → 1.12
                y_offset = -16.0 * math.sin(math.pi * st)
            else:
                rt       = (lt - 0.55) / 0.45
                damping  = (1.0 - rt) ** 2
                y_squash = 1.0 + 0.07 * math.cos(math.pi * rt * 4) * damping
            shadow_alpha = max(18, int(60 - 35 * abs(y_offset / 16.0)))

        elif self.held:
            # Slow sinusoidal glow pulse on held dice
            glow_alpha = int(28 + 22 * math.sin(math.pi * 2 * self.pulse_t))

        # ── Held glow halo ────────────────────────────────────────────────
        if glow_alpha > 0:
            r, g, b = accent_rgb
            p.save()
            p.setPen(Qt.PenStyle.NoPen)
            for spread, alpha in [(10, glow_alpha // 3), (6, glow_alpha // 2), (3, glow_alpha)]:
                p.setBrush(QBrush(QColor(r, g, b, alpha)))
                p.drawRoundedRect(
                    QRectF(cx - self.SIZE / 2 - spread,
                           die_cy - self.SIZE / 2 - spread,
                           self.SIZE + spread * 2,
                           self.SIZE + spread * 2),
                    12, 12
                )
            p.restore()

        # ── Drop shadow ────────────────────────────────────────────────────
        if not self.blank:
            sw = int((self.SIZE * x_scale if (self.rolling and not self.anim_settled)
                      else self.SIZE) * 0.78)
            sw = max(4, sw)
            sh = max(3, int(8 * (2.0 - y_squash)))
            sx = int(cx - sw / 2)
            sy = int(die_cy + self.SIZE * 0.5 * y_squash + y_offset)
            p.save()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, shadow_alpha)))
            p.drawEllipse(sx, sy, sw, sh)
            p.restore()

        # ── Background rect ────────────────────────────────────────────────
        p.save()
        active_rolling = self.rolling and not self.anim_settled
        rect_w = max(6.0, (self.SIZE * x_scale + 8) if active_rolling else float(self.SIZE + 8))
        rect_x = cx - rect_w / 2.0
        if self.held:
            r, g, b = accent_rgb
            border_alpha = int(180 + 60 * math.sin(math.pi * 2 * self.pulse_t))
            p.setPen(QPen(QColor(r, g, b, border_alpha), 3))
            p.setBrush(QBrush(QColor(r, g, b, 25 + glow_alpha // 2)))
        elif active_rolling:
            a = int(65 * opacity * max(0.2, x_scale))
            p.setPen(QPen(QColor(255, 255, 255, a), 1))
            p.setBrush(QBrush(QColor(255, 255, 255, max(0, a - 50))))
        else:
            p.setPen(QPen(QColor("#ffffff22"), 1))
            p.setBrush(QBrush(QColor(255, 255, 255, 10)))
        p.drawRoundedRect(QRectF(rect_x, 2, rect_w, self.SIZE + 4), 10, 10)
        p.restore()

        # ── Die face ────────────────────────────────────────────────────────
        if not self.blank:
            pix    = self._render_face(display_face, accent_hex if self.held else "#ffffff")
            draw_w = max(1, int(self.SIZE * x_scale))
            draw_h = max(1, int(self.SIZE * y_squash))
            draw_x = int(cx - draw_w / 2)
            draw_y = int(die_cy - draw_h / 2 + y_offset)
            p.save()
            if active_rolling:
                p.setOpacity(opacity)
            p.drawPixmap(draw_x, draw_y, draw_w, draw_h, pix)
            p.restore()

    # ---------------------------------------------------------------- state --
    def set_face(self, face: int, held: bool = False, rolling: bool = False,
                 accent: str = "#e94560"):
        self.blank       = False
        self.face        = face
        self.visual_face = face
        self.held        = held
        self.rolling     = rolling
        self.held_label.setVisible(held)
        self.update()

    def set_blank(self):
        self.blank        = True
        self.rolling      = False
        self.anim_t       = 0.0
        self.anim_settled = False
        self.spin_angle   = 0.0
        self.snap_t       = -1.0
        self.land_t       = -1.0
        self.pulse_t      = 0.0
        self.held_label.hide()
        self.update()

    def mousePressEvent(self, event):
        self.clicked_signal()

    def clicked_signal(self):
        pass

# ============================================================================
# ROLLER — HistoryRow
# ============================================================================
class RollerHistoryRow(QWidget):
    def __init__(self, player, dice, label, score, accent, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        if player:
            name_lbl = QLabel(player)
            name_lbl.setStyleSheet(
                "color: rgba(255,255,255,0.45); font-size: 10px; font-style: italic;"
            )
            layout.addWidget(name_lbl)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 12px;")
        layout.addWidget(lbl, 1)

        # Mini dice
        for d in dice:
            w = QSvgWidget()
            w.setFixedSize(18, 18)
            w.load(QByteArray(_make_roller_svg(d, accent)))
            layout.addWidget(w)

        pts = QLabel(f"{score} pts")
        pts.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        layout.addWidget(pts)

        self.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 8px;")


# ============================================================================
# ROLLER — quick-score helper
# ============================================================================
def _roller_score(dice):
    counts = Counter(dice)
    total  = sum(dice)
    vals   = sorted(counts.values(), reverse=True)
    uniq   = sorted(set(dice))
    if vals[0] == 5:
        return ("YAHTZII! 🎲", 50)
    if vals[0] == 4:
        return ("Four of a Kind", total)
    if vals[0] == 3 and len(vals) > 1 and vals[1] == 2:
        return ("Full House", 25)
    if vals[0] == 3:
        return ("Three of a Kind", total)
    if len(uniq) == 5:
        span = uniq[-1] - uniq[0]
        if span == 4: return ("Large Straight", 40)
    _SMALL_RUNS = [(1,2,3,4), (2,3,4,5), (3,4,5,6)]
    if any(all(s in uniq for s in seq) for seq in _SMALL_RUNS):
        return ("Small Straight", 30)
    if vals[0] == 2:
        return ("One Pair", total)
    return ("Chance", total)


# ============================================================================
# ROLLER — Main widget
# ============================================================================
class YahtzeeRollerWidget(QWidget):
    """
    Animated dice roller (from roll.py).

    When scorecard_mode=True it shows a player banner and a
    "Done — Use These Dice" button. The scorecard connects
    on_turn_done(dice) to receive the confirmed roll.
    """

    CHARGE_DURATION  = 600
    ROLL_DURATION_MIN= 600
    ROLL_DURATION_MAX= 1200
    TICK_MS          = 16

    def __init__(self, scorecard_mode: bool = False, parent=None):
        super().__init__(parent)
        self.scorecard_mode = scorecard_mode
        self.setWindowTitle("Pro Yahtzii Roller")
        h = 780 if scorecard_mode else 720
        self.setFixedSize(520, h)
        self.setAutoFillBackground(True)

        self.dice          = [1, 1, 1, 1, 1]
        self.held          = [False] * 5
        self.rolls_left    = 3
        self.state         = "IDLE"
        self.start_time    = None
        self.roll_duration = 800
        self.history       = []
        self.current_theme = "Classic"
        self.current_player = ""   # set by prepare_for_player in scorecard mode
        self.on_turn_done  = None   # callable(dice)

        self._build_ui()
        self._apply_theme()
        self._update_roll_pips()

    # ---------------------------------------------------------------- UI ----
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(8)

        if self.scorecard_mode:
            self.player_banner = QLabel("")
            self.player_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.player_banner.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {CLR_ACTIVE_TURN}; "
                f"border: 1px solid {CLR_ACTIVE_TURN}44; border-radius: 6px; padding: 6px;"
            )
            root.addWidget(self.player_banner)

        subtitle = QLabel("PRO EDITION")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 10px; letter-spacing: 6px; color: rgba(255,255,255,0.4); font-family: monospace;"
        )
        root.addWidget(subtitle)

        self.title_label = QLabel("YAHTZII")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Georgia", 36, QFont.Weight.Black))
        root.addWidget(self.title_label)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(6)
        self.theme_buttons = {}
        for name in _ROLLER_THEMES:
            btn = QPushButton(name)
            btn.setFixedHeight(24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self._set_theme(n))
            self.theme_buttons[name] = btn
            if not self.scorecard_mode:
                theme_row.addWidget(btn)
        if not self.scorecard_mode:
            root.addLayout(theme_row)

        self.status_label = QLabel("Press ROLL to start!")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: white; min-height: 28px;"
        )
        root.addWidget(self.status_label)

        bar_hdr = QHBoxLayout()
        bl = QLabel("POWER")
        bl.setStyleSheet(
            "font-size: 10px; letter-spacing: 3px; color: rgba(255,255,255,0.5); font-family: monospace;"
        )
        self.energy_pct_label = QLabel("0%")
        self.energy_pct_label.setStyleSheet(
            "font-size: 10px; color: rgba(255,255,255,0.5); font-family: monospace;"
        )
        bar_hdr.addWidget(bl); bar_hdr.addStretch(); bar_hdr.addWidget(self.energy_pct_label)
        root.addLayout(bar_hdr)

        self.energy_bar = QProgressBar()
        self.energy_bar.setRange(0, 100); self.energy_bar.setValue(0)
        self.energy_bar.setTextVisible(False); self.energy_bar.setFixedHeight(10)
        root.addWidget(self.energy_bar)

        dice_row = QHBoxLayout()
        dice_row.setSpacing(8)
        dice_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.die_widgets = []
        for i in range(5):
            dw = DieWidget(i)
            dw.clicked_signal = (lambda idx=i: lambda: self._toggle_hold(idx))()
            self.die_widgets.append(dw)
            dice_row.addWidget(dw)
        root.addLayout(dice_row)

        self.hold_hint = QLabel("Tap a die to hold / unhold it")
        self.hold_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hold_hint.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.35);")
        self.hold_hint.hide()
        root.addWidget(self.hold_hint)

        pips_row = QHBoxLayout()
        pips_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pips_row.setSpacing(8)
        self.pip_labels = []
        for _ in range(3):
            p = QLabel("●")
            p.setStyleSheet("font-size: 14px;")
            self.pip_labels.append(p)
            pips_row.addWidget(p)
        rolls_lbl = QLabel("rolls left")
        rolls_lbl.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.5);")
        pips_row.addWidget(rolls_lbl)
        root.addLayout(pips_row)

        self.result_frame = QFrame()
        self.result_frame.setStyleSheet(
            "background: rgba(255,255,255,0.06); border-radius: 10px;"
        )
        res_layout = QVBoxLayout(self.result_frame)
        res_layout.setContentsMargins(16, 10, 16, 10)
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet(
            "font-size: 20px; font-weight: 900; letter-spacing: 1px;"
        )
        self.result_score_label = QLabel("")
        self.result_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_score_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7);")
        res_layout.addWidget(self.result_label)
        res_layout.addWidget(self.result_score_label)
        self.result_frame.hide()
        root.addWidget(self.result_frame)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.roll_button = QPushButton("ROLL")
        self.roll_button.setFixedHeight(52)
        self.roll_button.setMinimumWidth(160)
        self.roll_button.setFont(QFont("Georgia", 16, QFont.Weight.Black))
        self.roll_button.pressed.connect(self._start_charge)
        btn_row.addWidget(self.roll_button)

        if not self.scorecard_mode:
            self.new_round_btn = QPushButton("NEW ROUND")
            self.new_round_btn.setFixedHeight(52)
            self.new_round_btn.setFont(QFont("Georgia", 12))
            self.new_round_btn.clicked.connect(self._new_round)
            self.new_round_btn.setStyleSheet("""
                QPushButton { background: rgba(255,255,255,0.08); color: white;
                              border: 1px solid rgba(255,255,255,0.18); border-radius: 10px; }
                QPushButton:hover { background: rgba(255,255,255,0.14); }
            """)
            btn_row.addWidget(self.new_round_btn)
        root.addLayout(btn_row)

        if self.scorecard_mode:
            self.use_dice_btn = QPushButton("✔  Done — Use These Dice")
            self.use_dice_btn.setFixedHeight(46)
            self.use_dice_btn.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
            self.use_dice_btn.setStyleSheet(
                f"QPushButton {{ background: {CLR_VALID}; color: #0a1a0a; "
                f"border-radius: 10px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: #6ee7b7; }}"
                f"QPushButton:disabled {{ background: rgba(255,255,255,0.1); "
                f"color: rgba(255,255,255,0.3); }}"
            )
            self.use_dice_btn.setEnabled(False)
            self.use_dice_btn.clicked.connect(self._confirm_dice)
            root.addWidget(self.use_dice_btn)

        hist_title = QLabel("HISTORY")
        hist_title.setStyleSheet(
            "font-size: 10px; letter-spacing: 4px; color: rgba(255,255,255,0.4); font-family: monospace;"
        )
        root.addWidget(hist_title)

        self.history_layout = QVBoxLayout()
        self.history_layout.setSpacing(4)
        root.addLayout(self.history_layout)
        root.addStretch()

        self.timer = QTimer(self)
        self.timer.setInterval(self.TICK_MS)
        self.timer.timeout.connect(self._update_animation)

        # Separate timer that keeps running for the landing bounce after roll ends
        self._bounce_timer = QTimer(self)
        self._bounce_timer.setInterval(self.TICK_MS)
        self._bounce_timer.timeout.connect(self._tick_bounce)
        self._land_start = time.perf_counter()

        # Idle pulse timer for held dice between rolls
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(30)   # ~33 fps is plenty for a slow glow
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start()

    # --------------------------------------------------------------- theme --
    def _apply_theme(self):
        th  = _ROLLER_THEMES[self.current_theme]
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(th["bg"]))
        self.setPalette(pal)
        accent = th["accent"]
        self.title_label.setStyleSheet(
            f"font-size: 38px; font-weight: 900; color: {accent}; font-family: Georgia;"
        )
        self.roll_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {th['bar_start']}, stop:1 {th['bar_end']});
                color: white; border: none; border-radius: 10px;
                font-weight: 900; font-size: 16px;
            }}
            QPushButton:disabled {{
                background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.3);
            }}
        """)
        self.energy_bar.setStyleSheet(f"""
            QProgressBar {{ border: none; border-radius: 5px;
                            background: rgba(255,255,255,0.1); }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {th['bar_start']}, stop:1 {th['bar_end']});
                border-radius: 5px;
            }}
        """)
        self.result_label.setStyleSheet(
            f"font-size: 20px; font-weight: 900; color: {accent}; letter-spacing: 1px;"
        )
        for name, btn in self.theme_buttons.items():
            if name == self.current_theme:
                btn.setStyleSheet(f"""
                    QPushButton {{ background: rgba(255,255,255,0.12); color: {accent};
                        border: 2px solid {accent}; border-radius: 12px;
                        font-size: 11px; font-weight: bold; padding: 2px 10px; }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton { background: transparent; color: rgba(255,255,255,0.6);
                        border: 1px solid rgba(255,255,255,0.2); border-radius: 12px;
                        font-size: 11px; padding: 2px 10px; }
                    QPushButton:hover { background: rgba(255,255,255,0.08); }
                """)
        self._update_dice_display()
        self._update_roll_pips()

    def _set_theme(self, name: str):
        self.current_theme = name
        self._apply_theme()
        if callable(self.on_theme_changed):
            self.on_theme_changed(name)

    # on_theme_changed is set by the scorecard; default is a no-op
    on_theme_changed = lambda self, name: None

    # --------------------------------------------------------------- dice ---
    def _update_dice_display(self):
        accent  = _ROLLER_THEMES[self.current_theme]["accent"]
        rolling = (self.state == "ROLLING")
        for i, dw in enumerate(self.die_widgets):
            if not rolling or self.held[i]:
                # Not rolling or held: set state directly and repaint
                dw.rolling      = False
                dw.anim_settled = True
                dw.blank        = dw.blank and (self.rolls_left == 3)  # keep blank only pre-roll
                dw.face         = self.dice[i]
                dw.held         = self.held[i]
            dw.update()

    def _toggle_hold(self, i: int):
        if self.state != "IDLE" or self.rolls_left == 3:
            return
        self.held[i] = not self.held[i]
        self._update_dice_display()

    def _roll_free_dice(self):
        for i in range(5):
            if not self.held[i]:
                self.dice[i] = random.randint(1, 6)

    # --------------------------------------------------------- animation ----
    def _start_charge(self):
        if self.state != "IDLE" or self.rolls_left == 0:
            return
        self.roll_duration = random.randint(self.ROLL_DURATION_MIN, self.ROLL_DURATION_MAX)
        self.state = "CHARGING"
        self.start_time = time.perf_counter()
        self.roll_button.setEnabled(False)
        if self.scorecard_mode:
            self.use_dice_btn.setEnabled(False)
        self.status_label.setText("Blowing Dice...")
        self.timer.start()

    def _update_animation(self):
        now        = time.perf_counter()
        elapsed_ms = (now - self.start_time) * 1000

        if self.state == "CHARGING":
            t = min(elapsed_ms / self.CHARGE_DURATION, 1.0)
            self.energy_bar.setValue(int(t * 100))
            self.energy_pct_label.setText(f"{int(t * 100)}%")
            if t >= 1.0:
                self._start_roll()
            return

        if self.state != "ROLLING":
            return

        dt_ms = (now - self._last_frame_time) * 1000
        self._last_frame_time = now

        t_global    = min(elapsed_ms / self.roll_duration, 1.0)
        all_settled = True

        for i, dw in enumerate(self.die_widgets):
            if self.held[i]:
                # Pulse held dice even while others are rolling
                dw.pulse_t = (dw.pulse_t + dt_ms / 1800.0) % 1.0
                dw.update()
                continue

            settle_t  = self._die_settle[i]
            t_die     = min(t_global / settle_t, 1.0) if settle_t > 0 else 1.0
            dw.anim_t = t_die

            if not dw.anim_settled:
                all_settled = False

                ease          = 1.0 - (1.0 - t_die) ** 3
                current_speed = self._die_spin_speed[i] * (1.0 - ease)

                prev_angle    = dw.spin_angle
                dw.spin_angle += current_speed * dt_ms

                # On each 180° crossing swap the shown face.
                # In the last 25% of this die's roll, bias toward the final
                # face so the result feels earned rather than arbitrary.
                prev_half = int(prev_angle / 180)
                curr_half = int(dw.spin_angle / 180)
                if curr_half > prev_half:
                    final = self._die_final[i]
                    bias  = ease        # 0 → 1 over the roll
                    # Show final face with increasing probability as die slows
                    if random.random() < bias * 0.65:
                        dw.visual_face = final
                    else:
                        dw.visual_face = random.randint(1, 6)

                if t_die >= 1.0:
                    dw.anim_settled = True
                    dw.rolling      = False
                    self.dice[i]    = self._die_final[i]
                    dw.face         = self._die_final[i]
                    dw.visual_face  = self._die_final[i]
                    # Begin smooth snap to nearest face-forward angle
                    nearest         = round(dw.spin_angle / 360) * 360
                    dw.snap_target  = nearest
                    dw.snap_t       = 0.0
                    dw._snap_start  = now
                    # Trigger landing bounce with this die's own timestamp
                    dw.land_t       = 0.0
                    dw.land_start   = now
                else:
                    dw.rolling = True

            else:
                # Advance snap tween
                if 0.0 <= dw.snap_t < 1.0:
                    dw.snap_t = min((now - dw._snap_start) * 1000 / dw.SNAP_DUR, 1.0)
                    if dw.snap_t >= 1.0:
                        dw.spin_angle = dw.snap_target

                # Advance landing bounce
                if 0.0 <= dw.land_t < 1.0:
                    dw.land_t = min((now - dw.land_start) * 1000 / dw.LAND_DUR, 1.0)

            dw.blank = False
            dw.update()

        if t_global >= 1.0 or all_settled:
            for i, dw in enumerate(self.die_widgets):
                if not self.held[i]:
                    self.dice[i]    = self._die_final[i]
                    dw.face         = self._die_final[i]
                    dw.visual_face  = self._die_final[i]
                    dw.rolling      = False
                    dw.anim_settled = True
                    dw.blank        = False
                    if dw.snap_t < 0.0:
                        dw.spin_angle = round(dw.spin_angle / 360) * 360
                    dw.update()
            self.timer.stop()
            self._finish_roll()

    def _start_roll(self):
        self.state      = "ROLLING"
        self.start_time = time.perf_counter()
        self.status_label.setText("Rolling...")

        # Pre-compute final faces and per-die settle fractions
        self._die_final = [
            self.dice[i] if self.held[i] else random.randint(1, 6)
            for i in range(5)
        ]
        # Stagger settle points: 65%–100% of total duration, shuffled
        settle_points = sorted([random.uniform(0.65, 1.00) for _ in range(5)])
        random.shuffle(settle_points)
        self._die_settle = settle_points

        # Per-die initial spin speed (degrees/ms) — varies for natural feel
        self._die_spin_speed = [
            random.uniform(1.4, 2.6) if not self.held[i] else 0.0
            for i in range(5)
        ]
        # Track last frame time for delta-time spin updates
        self._last_frame_time = time.perf_counter()

        # Kick off rolling state on each free die
        for i, dw in enumerate(self.die_widgets):
            if not self.held[i]:
                dw.rolling      = True
                dw.anim_t       = 0.0
                dw.anim_settled = False
                dw.blank        = False
                dw.spin_angle   = random.uniform(0, 360)
                dw.visual_face  = dw.face
                dw.land_t       = -1.0
                dw.land_start   = 0.0
                dw.snap_t       = -1.0
                dw._snap_start  = 0.0
                dw.pulse_t      = 0.0

    def _finish_roll(self):
        self.state = "IDLE"
        self.energy_bar.setValue(0)
        self.energy_pct_label.setText("0%")
        self.rolls_left -= 1
        self._update_dice_display()
        self._update_roll_pips()

        # Keep repainting for the landing bounce duration
        self._bounce_timer.start(self.TICK_MS)

        if self.rolls_left == 0:
            label, pts = _roller_score(self.dice)
            self.status_label.setText(f"Round over!  {label} — {pts} pts")
            self._show_result(label, pts)
            self._add_history(list(self.dice), label, pts)
            self.roll_button.setEnabled(False)
            self.hold_hint.hide()
            if self.scorecard_mode:
                self.use_dice_btn.setEnabled(True)
        else:
            rolls_word = "roll" if self.rolls_left == 1 else "rolls"
            self.status_label.setText(
                f"{self.rolls_left} {rolls_word} left — hold dice to keep them"
            )
            self.result_frame.hide()
            self.roll_button.setEnabled(True)
            self.hold_hint.show()
            if self.scorecard_mode:
                self.use_dice_btn.setEnabled(True)   # can confirm early

    def _show_result(self, label: str, pts: int):
        self.result_label.setText(label)
        self.result_score_label.setText(f"{pts} points")
        accent = _ROLLER_THEMES[self.current_theme]["accent"]
        self.result_label.setStyleSheet(
            f"font-size: 20px; font-weight: 900; color: {accent}; letter-spacing: 1px;"
        )
        self.result_frame.show()

    def _tick_bounce(self):
        """Drives landing bounce, snap tween, and held pulse repaints after roll ends."""
        now      = time.perf_counter()
        all_done = True

        for dw in self.die_widgets:
            needs_update = False

            # Landing bounce (per-die timestamp)
            if 0.0 <= dw.land_t < 1.0:
                dw.land_t = min((now - dw.land_start) * 1000 / dw.LAND_DUR, 1.0)
                needs_update = True
                if dw.land_t < 1.0:
                    all_done = False

            # Snap tween
            if 0.0 <= dw.snap_t < 1.0:
                dw.snap_t = min((now - dw._snap_start) * 1000 / dw.SNAP_DUR, 1.0)
                if dw.snap_t >= 1.0:
                    dw.spin_angle = dw.snap_target
                needs_update = True
                if dw.snap_t < 1.0:
                    all_done = False

            # Held pulse — keep running indefinitely for held dice
            if dw.held:
                dw.pulse_t = (dw.pulse_t + self.TICK_MS / 1800.0) % 1.0
                needs_update = True
                all_done = False

            if needs_update:
                dw.update()

        if all_done:
            self._bounce_timer.stop()

    def _tick_pulse(self):
        """Keeps held dice pulsing between rolls."""
        if self.state != "IDLE":
            return
        any_held = False
        for i, dw in enumerate(self.die_widgets):
            if self.held[i] and not dw.rolling:
                dw.pulse_t = (dw.pulse_t + 30.0 / 1800.0) % 1.0
                dw.update()
                any_held = True

    def _update_roll_pips(self):
        accent = _ROLLER_THEMES[self.current_theme]["accent"]
        for i, pip in enumerate(self.pip_labels):
            if i < self.rolls_left:
                pip.setStyleSheet(f"font-size: 14px; color: {accent};")
            else:
                pip.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.2);")

    def _add_history(self, dice, label, pts):
        self.history.insert(0, (self.current_player, dice, label, pts))
        self.history = self.history[:6]
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        accent = _ROLLER_THEMES[self.current_theme]["accent"]
        for player, d, l, s in self.history:
            self.history_layout.addWidget(RollerHistoryRow(player, d, l, s, accent))

    def update_last_history_label(self, category: str, pts: int):
        """Replace the top history entry's label/score with the actual scorecard category chosen."""
        if not self.history:
            return
        player, dice, _, _ = self.history[0]
        self.history[0] = (player, dice, category, pts)
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        accent = _ROLLER_THEMES[self.current_theme]["accent"]
        for p, d, l, s in self.history:
            self.history_layout.addWidget(RollerHistoryRow(p, d, l, s, accent))

    def _new_round(self):
        self.timer.stop()
        self._bounce_timer.stop()
        self._pulse_timer.start()  # keep pulsing for any held dice
        self.dice       = [random.randint(1, 6) for _ in range(5)]
        self.held       = [False] * 5
        self.rolls_left = 3
        self.state      = "IDLE"
        self.energy_bar.setValue(0)
        self.energy_pct_label.setText("0%")
        self.result_frame.hide()
        self.hold_hint.hide()
        self.status_label.setText("New round! Press ROLL.")
        self.roll_button.setEnabled(True)
        if self.scorecard_mode:
            self.use_dice_btn.setEnabled(False)
            for dw in self.die_widgets:
                dw.held = False
                dw.set_blank()
        else:
            self._update_dice_display()
        self._update_roll_pips()

    # --------------------------------- scorecard integration ----------------
    def _confirm_dice(self):
        # Record history if the player finishes early (rolls_left > 0)
        # When rolls_left == 0 it was already recorded in _finish_roll.
        if self.rolls_left > 0:
            label, pts = _roller_score(self.dice)
            self._add_history(list(self.dice), label, pts)
        if self.on_turn_done:
            self.on_turn_done(list(self.dice))

    def prepare_for_player(self, player_name: str):
        """Reset for a new player's turn and update the banner."""
        self.current_player = player_name
        self._new_round()
        if self.scorecard_mode and hasattr(self, "player_banner"):
            self.player_banner.setText(f"🎲  {player_name}'s Turn")

    def closeEvent(self, event):
        """
        In scorecard mode, closing the window just hides it so the roll state
        is preserved.  The scorecard's 'Open Roller' button will re-show it.
        The scorecard is notified so it can re-enable the button.
        """
        if self.scorecard_mode:
            event.ignore()
            self.hide()
            if callable(self.on_window_hidden):
                self.on_window_hidden()
        else:
            event.accept()

    # on_window_hidden is set by the scorecard; default is a no-op
    on_window_hidden = lambda self: None


# ============================================================================
# RULES DIALOG
# ============================================================================
class RulesDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Official Yahtzii Rules")
        self.resize(660, 750)
        layout = QVBoxLayout(self)
        rules_text = QTextEdit()
        rules_text.setReadOnly(True)
        rules_text.setHtml("""
            <h2 style='color: #3B82F6;'>Yahtzii Pro — How to Use This App</h2>

            <h3 style='color: #93C5FD;'>Object of the Game</h3>
            <p>Score the highest total across all 13 categories. Highest Grand Total wins.</p>

            <h3 style='color: #93C5FD;'>Setting Up — Registration</h3>
            <p>Enter each player's name (up to 8). Tick <b>🎲 Use Digital Roller</b> to use
            the animated roller window instead of physical dice for every turn.</p>

            <h3 style='color: #93C5FD;'>Digital Roller Mode</h3>
            <ol>
                <li>The roller window opens automatically at the start of each turn, showing
                    whose turn it is.</li>
                <li>Press <b>ROLL</b> (hold to charge the power bar). Click any dice to
                    <b>hold</b> them, then press <b>ROLL</b> again (up to 3 rolls total).</li>
                <li>You may confirm at any point — you don't have to use all 3 rolls.</li>
                <li>Click <b>Done — Use These Dice</b> to lock in the roll. The scorecard
                    unlocks and you choose a category normally.</li>
            </ol>
            <p>The <b>🎲 Open Roller</b> button on the scorecard lets you re-open the roller
            window at any time during your turn if you accidentally close it.</p>

            <h3 style='color: #93C5FD;'>Physical Dice Mode</h3>
            <p>Roll your own dice, then select a score from the dropdown in your column.</p>

            <h3 style='color: #93C5FD;'>Roll-Off for Order</h3>
            <p>Click <b>🎲 Roll for All Players</b> to animate a virtual roll and sort players
            by total. Ties trigger an automatic re-roll. Or click <b>Start Scoring</b> to use
            registration order.</p>

            <h3 style='color: #93C5FD;'>Upper Section (Ones–Sixes)</h3>
            <p>Select the count of matching dice. The app multiplies by face value.
            Score 63+ for a <b>+35 bonus</b>.</p>

            <h3 style='color: #93C5FD;'>Lower Section</h3>
            <ul>
                <li><b>3 / 4 of a Kind</b> — total of all 5 dice</li>
                <li><b>Full House</b> — fixed 25 pts</li>
                <li><b>Small Straight</b> — fixed 30 pts</li>
                <li><b>Large Straight</b> — fixed 40 pts</li>
                <li><b>Yahtzii</b> — fixed 50 pts</li>
                <li><b>Chance</b> — total of all 5 dice</li>
            </ul>

            <h3 style='color: #93C5FD;'>Yahtzii Bonus &amp; Joker Rules</h3>
            <p>Second+ Yahtzii (Yahtzii box = 50): click <b>+</b> in Yahtzii Bonus row.
            Follow the on-screen Joker banner for priority order.</p>

            <h3 style='color: #93C5FD;'>Correcting a Score</h3>
            <p>Reset a claimed cell to <b>—</b>, correct it, then score your actual turn.
            Corrections are free edits and do not consume your turn.</p>

            <h3 style='color: #93C5FD;'>Play Again</h3>
            <p>▶ Same Order — instant restart · 🎲 Roll for Order — new roll-off ·
            📋 New Game / Change Players — back to registration · ✖ Quit</p>
        """)
        layout.addWidget(rules_text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


class PlayerSetupDialog(QDialog):
    def __init__(self, prefill=None, initial_theme="Classic"):
        super().__init__()
        self.setWindowTitle("Yahtzii Registration")
        self.setFixedSize(420, 650)
        self.player_inputs   = []
        self._selected_theme = initial_theme if initial_theme in _ROLLER_THEMES else "Classic"
        self._theme_btns     = {}
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("Player Registration")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        self.hint_lbl = QLabel("💡 If rolling manually, enter players in desired turn order.")
        self.hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_lbl.setStyleSheet("font-size: 11px; padding-bottom: 4px;")
        layout.addWidget(self.hint_lbl)

        self.scroll_area   = QScrollArea()
        self.scroll_widget = QWidget()
        self.input_layout  = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ Add Player")
        self.add_btn.clicked.connect(lambda _: self.add_player_slot())
        self.rem_btn = QPushButton("- Remove Player")
        self.rem_btn.clicked.connect(lambda _: self.remove_player_slot())
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.rem_btn)
        layout.addLayout(btn_layout)

        for name in (prefill or [""]):
            self.add_player_slot(name if name else "")

        # ── Digital Roller ───────────────────────────────────────────────
        self.roller_frame = QFrame()
        self.roller_frame.setObjectName("innerFrame")
        roller_inner = QVBoxLayout(self.roller_frame)
        roller_inner.setContentsMargins(12, 10, 12, 10)
        self.use_roller_chk = QCheckBox("🎲  Use Digital Roller (fully digital experience)")
        self.use_roller_chk.setStyleSheet("font-weight: bold; font-size: 12px;")
        roller_inner.addWidget(self.use_roller_chk)
        layout.addWidget(self.roller_frame)

        # ── Theme picker ─────────────────────────────────────────────────
        self.theme_frame = QFrame()
        self.theme_frame.setObjectName("innerFrame")
        theme_inner = QVBoxLayout(self.theme_frame)
        theme_inner.setContentsMargins(12, 10, 12, 10)
        theme_inner.setSpacing(6)

        self.theme_title_lbl = QLabel("🎨  Theme:")
        self.theme_title_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
        theme_inner.addWidget(self.theme_title_lbl)

        self.theme_row_1 = QHBoxLayout()
        self.theme_row_1.setSpacing(5)
        self.theme_row_2 = QHBoxLayout()
        self.theme_row_2.setSpacing(5)

        theme_names = list(_ROLLER_THEMES.keys())
        for i, tname in enumerate(theme_names):
            btn = QPushButton(tname)
            btn.setFixedHeight(28)
            btn.setMinimumWidth(72)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, n=tname: self._pick_theme(n))
            self._theme_btns[tname] = btn

            if i < 5:
                self.theme_row_1.addWidget(btn)
            else:
                self.theme_row_2.addWidget(btn)

        theme_inner.addLayout(self.theme_row_1)
        theme_inner.addLayout(self.theme_row_2)
        layout.addWidget(self.theme_frame)

        self.next_btn = QPushButton("Next: Determine Order")
        self.next_btn.clicked.connect(self.accept)
        layout.addWidget(self.next_btn)

        self._apply_theme(self._selected_theme)

    def _pick_theme(self, name: str):
        self._selected_theme = name
        self._apply_theme(name)

    def _apply_theme(self, name: str):
        import colorsys
        th     = _ROLLER_THEMES[name]
        bg     = th["bg"]
        accent = th["accent"]
        start  = th["bar_start"]
        end    = th["bar_end"]

        def _darken(hx, f):
            hx = hx.lstrip("#")
            r, g, b = (int(hx[i:i+2], 16) / 255 for i in (0, 2, 4))
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v * f)
            return "#{:02x}{:02x}{:02x}".format(int(r2 * 255), int(g2 * 255), int(b2 * 255))

        cell   = _darken(bg, 1.40)
        active = _darken(bg, 1.65)
        table  = _darken(bg, 1.15) if bg != "#1a1a1a" else "#1e1e1e"

        self.setStyleSheet(f"""
            QDialog                  {{ background-color: {bg}; color: #F1F5F9; }}
            QWidget                  {{ background-color: {bg}; color: #F1F5F9; }}
            QScrollArea              {{ background-color: {bg}; border: none; }}
            QAbstractScrollArea      {{ background-color: {bg}; }}
            QAbstractScrollArea > QWidget > QWidget {{ background-color: {bg}; }}
            QLineEdit                {{ background-color: {cell}; color: #F1F5F9;
                                        border: 1px solid {active}; border-radius: 3px;
                                        padding: 4px; }}
            QCheckBox                {{ color: #F1F5F9; background: transparent; }}
            QFrame#innerFrame        {{ background-color: {table}; border: 1px solid {active};
                                        border-radius: 6px; }}
            QPushButton              {{ background-color: {cell}; color: #F1F5F9;
                                        border-radius: 4px; padding: 6px 10px;
                                        font-weight: bold; border: none; }}
            QPushButton:hover        {{ background-color: {active}; }}
        """)

        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {start}, stop:1 {end});
                color: white; border-radius: 4px;
                padding: 10px; font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {end}, stop:1 {start}); }}
        """)

        for tname, btn in self._theme_btns.items():
            if tname == name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255,255,255,0.12);
                        color: {accent};
                        border: 2px solid {accent};
                        border-radius: 10px;
                        font-size: 10px;
                        font-weight: bold;
                        padding: 4px 6px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255,255,255,0.05);
                        color: #F1F5F9;
                        border: 1px solid rgba(255,255,255,0.18);
                        border-radius: 10px;
                        font-size: 10px;
                        font-weight: bold;
                        padding: 4px 6px;
                    }
                    QPushButton:hover {
                        background: rgba(255,255,255,0.12);
                    }
                """)

    def add_player_slot(self, name=""):
        if isinstance(name, bool) or name is None:
            name = ""
        elif not isinstance(name, str):
            name = str(name)

        if len(self.player_inputs) >= 8:
            QMessageBox.warning(self, "Max Players", "Maximum of 8 players allowed.")
            return
        row = QHBoxLayout()
        label = QLabel(f"Player {len(self.player_inputs) + 1}:")
        entry = QLineEdit()
        entry.setText(name)
        row.addWidget(label)
        row.addWidget(entry)
        self.input_layout.addLayout(row)
        self.player_inputs.append((label, entry))

    def remove_player_slot(self, checked=False):
        if len(self.player_inputs) <= 1:
            QMessageBox.warning(self, "Minimum Players", "At least one player is required.")
            return
        label, entry = self.player_inputs.pop()
        label.deleteLater()
        entry.deleteLater()

    def get_players(self):
        return [entry.text().strip() for _, entry in self.player_inputs if entry.text().strip()]

    def use_digital_roller_enabled(self):
        return self.use_roller_chk.isChecked()

    def selected_theme(self):
        return self._selected_theme

class RollOffDialog(QDialog):
    def __init__(self, names):
        super().__init__()
        self.setWindowTitle("Roll-Off for Order")
        self.setMinimumWidth(620)

        self.names             = names
        self.player_scores     = {name: [] for name in names}
        self.to_roll           = list(names)
        self.sorted_names      = list(names)
        self.animation_counter = 0
        self._reveal_queue     = []
        self._final_rolls      = {}
        self._order_score      = {}

        outer = QVBoxLayout(self)
        outer.setSpacing(12)
        outer.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🎲 Roll-Off for Order")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #3B82F6; padding-bottom: 4px;")
        outer.addWidget(title)

        self.info_lbl = QLabel("Roll to determine play order — highest total goes first.")
        self.info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        outer.addWidget(self.info_lbl)

        self.cards        = {}
        self.dice_labels  = {}
        self.score_labels = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        card_container   = QWidget()
        self.card_layout = QVBoxLayout(card_container)
        self.card_layout.setSpacing(8)
        scroll.setWidget(card_container)
        outer.addWidget(scroll)

        for name in names:
            self._build_card(name)

        self.btn_roll = QPushButton("🎲 Roll for All Players")
        self.btn_roll.setStyleSheet(accent_btn_style())
        self.btn_roll.clicked.connect(self.start_animation)
        outer.addWidget(self.btn_roll)

        self.btn_start = QPushButton("Start Scoring")
        self.btn_start.setStyleSheet(accent_btn_style())
        self.btn_start.clicked.connect(self.accept)
        outer.addWidget(self.btn_start)

        self.shake_timer  = QTimer(); self.shake_timer.timeout.connect(self._shake_tick)
        self.reveal_timer = QTimer(); self.reveal_timer.timeout.connect(self._reveal_next)
        self.adjustSize()

    def _build_card(self, name):
        card = QWidget()
        card.setStyleSheet(
            "background-color: #161B27; border: 1px solid #2E3F60; border-radius: 8px; padding: 6px;"
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
        for _ in range(5):
            dice_row.addStretch(1)
            d = QSvgWidget()
            d.setFixedSize(44, 44)
            d.load(QByteArray(_load_die_svg(1, "#1E2740")))
            dice_row.addWidget(d)
            dice_widgets.append(d)
        dice_row.addStretch(1)
        row.addLayout(dice_row)
        row.addStretch()

        score_lbl = QLabel("—")
        score_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        score_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        score_lbl.setStyleSheet("color: #64748B; min-width: 40px;")
        row.addWidget(score_lbl)

        self.card_layout.addWidget(card)
        self.cards[name]        = card
        self.dice_labels[name]  = dice_widgets
        self.score_labels[name] = score_lbl

    def _set_card_state(self, name, state):
        styles = {
            "idle":    ("border: 1px solid #2E3F60;",            "#94A3B8", "#64748B"),
            "rolling": (f"border: 2px solid {CLR_ACCENT};",      "white",   CLR_ACCENT),
            "done":    ("border: 1px solid #253354;",            "#CBD5E1", CLR_CLAIMED_TEXT),
            "tie":     (f"border: 2px solid {CLR_ACTIVE_TURN};", CLR_ACTIVE_TURN, CLR_ACTIVE_TURN),
            "winner":  (f"border: 2px solid {CLR_ACCENT};",      CLR_ACCENT, CLR_ACCENT),
        }
        border, name_color, score_color = styles.get(state, styles["idle"])
        self.cards[name].setStyleSheet(
            f"background-color: #161B27; {border} border-radius: 8px; padding: 6px;"
        )
        self.cards[name].findChild(QLabel).setStyleSheet(f"color: {name_color};")
        self.score_labels[name].setStyleSheet(f"color: {score_color}; min-width: 36px;")

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

    def _compute_final_rolls(self):
        self._final_rolls = {}
        for name in self.to_roll:
            dice = [random.randint(1, 6) for _ in range(5)]
            self._final_rolls[name] = (dice, sum(dice))
        self._reveal_queue = list(self.to_roll)
        self.reveal_timer.start(420)

    def _reveal_next(self):
        if not self._reveal_queue:
            self.reveal_timer.stop()
            self.finalize_roll()
            return
        name        = self._reveal_queue.pop(0)
        dice, total = self._final_rolls[name]
        for widget, v in zip(self.dice_labels[name], dice):
            widget.load(QByteArray(_load_die_svg(v, "#FFFFFF")))
        self.score_labels[name].setText(str(total))
        self._set_card_state(name, "done")

    def finalize_roll(self):
        for name in self.to_roll:
            _, roll = self._final_rolls[name]
            self.player_scores[name].append(roll)
            self._order_score[name] = roll

        score_groups = defaultdict(list)
        for n, s in {n: self.player_scores[n][-1] for n in self.to_roll}.items():
            score_groups[s].append(n)

        self.to_roll = [p for grp in score_groups.values() if len(grp) > 1 for p in grp]

        if not self.to_roll:
            self.sorted_names = sorted(
                self.names, key=lambda n: self._order_score.get(n, 0), reverse=True
            )
            for name in self.sorted_names:
                self.card_layout.removeWidget(self.cards[name])
                self.card_layout.addWidget(self.cards[name])
            for name in self.names:
                self._set_card_state(
                    name, "winner" if name == self.sorted_names[0] else "done"
                )
            self.info_lbl.setText(f"🏆 {self.sorted_names[0]} goes first!")
            self.info_lbl.setStyleSheet("color: #3B82F6; font-size: 12px; font-weight: bold;")
            self.btn_start.setStyleSheet(accent_btn_style())
        else:
            for name in self.to_roll:
                self._set_card_state(name, "tie")
            for name in self.names:
                if name not in self.to_roll:
                    self._set_card_state(name, "done")
            self.info_lbl.setText(f"⚠️  Tie! {', '.join(self.to_roll)} must re-roll.")
            self.info_lbl.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; font-size: 11px;")
            self.btn_roll.setText(f"🎲 Resolve Tie ({len(self.to_roll)} players)")
            self.btn_roll.setEnabled(True)


# ============================================================================
# GAME-OVER DIALOG
# ============================================================================
class GameOverDialog(QDialog):
    SAME_ORDER = 1
    ROLL_ORDER = 2
    QUIT       = 0
    NEW_GAME   = 3
    PLACE_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

    def __init__(self, scores, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Over!")
        self.setMinimumWidth(380)
        self.result_choice = self.QUIT
        solo = (len(scores) == 1)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        winner_name, winner_score = scores[0]
        if solo:
            msg = QLabel(f"🎲  {winner_name} — {winner_score} pts!")
        else:
            msg = QLabel(f"🏆  {winner_name} wins with {winner_score} pts!")
        msg.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding-bottom: 4px;")
        layout.addWidget(msg)

        for place, (name, score) in enumerate(scores, start=1):
            rw = QWidget()
            rw.setStyleSheet(
                f"background-color: {'#0C1A3A' if place == 1 else '#161B27'};"
                f"border: 1px solid {CLR_ACTIVE_TURN if place == 1 else '#2E3F60'};"
                f"border-radius: 6px;"
            )
            row = QHBoxLayout(rw)
            row.setContentsMargins(12, 6, 12, 6)
            pl = QLabel(self.PLACE_MEDALS.get(place, f"#{place}"))
            pl.setFont(QFont("Arial", 13)); pl.setFixedWidth(32)
            row.addWidget(pl)
            nl = QLabel(name)
            nl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            nl.setStyleSheet(f"color: {CLR_ACTIVE_TURN if place == 1 else '#CBD5E1'};")
            row.addWidget(nl); row.addStretch()
            sl = QLabel(f"{score} pts")
            sl.setFont(QFont("Arial", 11))
            sl.setStyleSheet(f"color: {CLR_ACTIVE_TURN if place == 1 else '#94A3B8'};")
            row.addWidget(sl)
            layout.addWidget(rw)

        layout.addSpacing(4)
        sub = QLabel("Play again?")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #94A3B8; font-size: 11px;")
        layout.addWidget(sub)

        # Solo: only offer Play Again and Quit (no order options)
        if solo:
            buttons = [
                ("▶  Play Again",              accent_btn_style(), self.SAME_ORDER),
                ("📋  New Game / Change Players","",                self.NEW_GAME),
                ("✖  Quit",                    "",                 self.QUIT),
            ]
        else:
            buttons = [
                ("▶  Same Order",              accent_btn_style(), self.SAME_ORDER),
                ("🎲  Roll for Order",          purple_btn_style(), self.ROLL_ORDER),
                ("📋  New Game / Change Players","",                self.NEW_GAME),
                ("✖  Quit",                    "",                 self.QUIT),
            ]

        for text, style, choice in buttons:
            btn = QPushButton(text)
            if style: btn.setStyleSheet(style)
            btn.clicked.connect(lambda _, c=choice: self._pick(c))
            layout.addWidget(btn)

        self.adjustSize()

    def _pick(self, choice):
        self.result_choice = choice
        self.accept()


# ============================================================================
# SCORECARD
# ============================================================================
class YahtzeeScorecard(QMainWindow):
    def __init__(self, players, use_digital_roller: bool = False, initial_theme: str = "Classic"):
        super().__init__()

        # ── REQUIRED: all theme vars must exist before setup_board() ──
        self._theme_accent    = CLR_ACCENT
        self._theme_table_bg  = CLR_TABLE
        self._theme_active    = CLR_ACTIVE_UNCLAIMED
        self._theme_unclaimed = CLR_UNCLAIMED
        self._theme_bg        = CLR_BACKGROUND
        self._current_theme_name = initial_theme

        self.players               = players
        self.current_turn_index    = 0
        self.play_again_requested  = False
        self._is_updating          = False
        self.joker_active          = False
        self._correction_pending   = False
        self._last_unclaimed_name  = ""
        self._correction_replaced_msg = ""
        self.use_digital_roller    = use_digital_roller
        self._roller               = None   # YahtzeeRollerWidget, created on demand
        self._roller_active        = False
        self._roller_dice          = None   # list[int] once roller confirms, None otherwise
        self._initial_theme        = initial_theme

        self.setWindowTitle("Yahtzii! Pro Scorecard")
        self.resize(1100, 900)
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 4, 8, 4)
        self.timer_label = QLabel("⏱  00:00")
        self.timer_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("color: #94A3B8; padding: 2px 8px;")
        top_bar.addWidget(self.timer_label)
        top_bar.addStretch()
        self.turn_timer_label = QLabel("🎲  00:00")
        self.turn_timer_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.turn_timer_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding: 2px 8px;")
        top_bar.addWidget(self.turn_timer_label)
        layout.addLayout(top_bar)

        # Banner
        self.turn_label = QLabel("")
        self.turn_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.turn_label.setStyleSheet(f"color: {CLR_ACTIVE_TURN}; padding: 4px;")
        self.turn_label.setVisible(False)
        layout.addWidget(self.turn_label)

        self.table = QTableWidget(len(ROW_LABELS), len(players))
        self.table.setVerticalHeaderLabels(ROW_LABELS)
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setup_board()
        layout.addWidget(self.table)

        # Bottom buttons
        btns = QHBoxLayout()
        for text, slot in [
            ("High Scores", self.show_high_scores),
            ("Reset",       self.reset),
            ("Rules",       self.show_rules),
        ]:
            b = QPushButton(text); b.clicked.connect(slot); btns.addWidget(b)

        if self.use_digital_roller:
            self.open_roller_btn = QPushButton("🎲 Open Roller")
            self.open_roller_btn.setStyleSheet(accent_btn_style())
            self.open_roller_btn.clicked.connect(self._open_roller_for_current_player)
            btns.addWidget(self.open_roller_btn)


        layout.addLayout(btns)

        # Status bar
        sb_widget    = QStatusBar()
        sb_widget.setSizeGripEnabled(False)
        sb_container = QWidget()
        sb_outer     = QVBoxLayout(sb_container)
        sb_outer.setContentsMargins(8, 3, 8, 3); sb_outer.setSpacing(1)
        self._sb_row1 = QLabel(); self._sb_row2 = QLabel()
        self._sb_row1.setTextFormat(Qt.TextFormat.RichText)
        self._sb_row2.setTextFormat(Qt.TextFormat.RichText)
        for lbl in (self._sb_row1, self._sb_row2):
            lbl.setStyleSheet(f"background-color: {CLR_TABLE}; font-size: 11px;")
        sb_outer.addWidget(self._sb_row1); sb_outer.addWidget(self._sb_row2)
        sb_widget.addWidget(sb_container, 1)
        sb_widget.setStyleSheet(
            f"QStatusBar {{ background-color: {CLR_TABLE}; border-top: 1px solid #2E3F60; }}"
            f"QStatusBar::item {{ border: none; }}"
        )
        self.setStatusBar(sb_widget)

        self._sb_data = {
            'leader': '', 'scores': '', 'last': '',
            'upper': '', 'upper_color': '#94A3B8',
            'best': '', 'streak': '', 'alltime': '',
        }
        self._load_alltime_high()
        self._streak_player  = None
        self._streak_count   = 0
        self._last_score_msg = ""

        # Apply initial theme immediately so colours are correct from the first frame
        # Safe defaults — immediately overwritten by apply_roller_theme below
        self._theme_accent    = CLR_ACCENT
        self._theme_unclaimed = CLR_UNCLAIMED
        self._theme_active    = CLR_ACTIVE_UNCLAIMED
        self._theme_bg        = CLR_BACKGROUND
        self._theme_table_bg  = CLR_TABLE
        self.apply_roller_theme(self._initial_theme)

        self.update_turn_ui()

        self._elapsed      = QElapsedTimer(); self._elapsed.start()
        self._turn_elapsed = QElapsedTimer(); self._turn_elapsed.start()
        self._clock        = QTimer()
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)

    # -------------------------------------------------------- roller glue ---
    def _open_roller_for_current_player(self):
        if self._roller is None:
            self._roller = YahtzeeRollerWidget(scorecard_mode=True)
            self._roller.on_turn_done     = self._on_roller_done
            self._roller.on_window_hidden = self._on_roller_hidden
            self._roller.on_theme_changed = self.apply_roller_theme
            # Sync roller to the theme chosen at registration
            self._roller._set_theme(self._initial_theme)

        player_name = self.players[self.current_turn_index]

        # Reopen after accidental close: the player already has a confirmed roll
        # (_roller_dice set) or is mid-roll (_roller_active was True when they
        # closed the window).  Just re-show without resetting anything.
        is_reopen = self._roller_dice is not None or self._roller_active

        if not is_reopen:
            # Fresh turn — reset the roller for this player
            self._roller.prepare_for_player(player_name)
            self._roller_active = True
            self.table.setEnabled(False)
            if hasattr(self, "open_roller_btn"):
                self.open_roller_btn.setEnabled(False)
            self.turn_label.setText(
                f"🎲 {player_name} is rolling… "
                f"click 'Done — Use These Dice' in the roller window."
            )
            self.turn_label.setStyleSheet(
                f"color: {CLR_ACTIVE_TURN}; border: 2px solid {CLR_ACTIVE_TURN}44; "
                f"padding: 6px; font-size: 11px;"
            )
            self.turn_label.setVisible(True)
        else:
            # Reopen — restore the correct banner depending on whether they
            # have already confirmed dice or are still mid-roll.
            if self._roller_dice is not None:
                # Roll already confirmed; table should be unlocked
                self.table.setEnabled(True)
                if hasattr(self, "open_roller_btn"):
                    self.open_roller_btn.setEnabled(True)
            else:
                # Still mid-roll; keep table locked
                self.table.setEnabled(False)
                if hasattr(self, "open_roller_btn"):
                    self.open_roller_btn.setEnabled(False)
                self.turn_label.setText(
                    f"🎲 {player_name} is rolling… "
                    f"click 'Done — Use These Dice' in the roller window."
                )
                self.turn_label.setStyleSheet(
                    f"color: {CLR_ACTIVE_TURN}; border: 2px solid {CLR_ACTIVE_TURN}44; "
                    f"padding: 6px; font-size: 11px;"
                )
                self.turn_label.setVisible(True)

        self._roller.show()
        self._roller.raise_()
        self._roller.activateWindow()

    def _on_roller_done(self, dice: list):
        self._roller_active = False
        self._roller.hide()

        self.table.setEnabled(True)
        if hasattr(self, "open_roller_btn"):
            self.open_roller_btn.setEnabled(True)

        self._roller_dice = dice   # drive row dimming in update_turn_ui

        faces       = "  ".join(str(d) for d in dice)
        player_name = self.players[self.current_turn_index]
        label, pts  = _roller_score(dice)
        self.turn_label.setText(
            f"🎲 {player_name} rolled [{faces}] — {label} ({pts} pts).  "
            f"Now choose a highlighted category to score."
        )
        self.turn_label.setStyleSheet(
            f"color: {CLR_VALID}; border: 2px solid {CLR_VALID}; "
            f"padding: 6px; font-size: 11px;"
        )
        self.turn_label.setVisible(True)
        self._last_score_msg = f"Rolled: [{faces}] — {label} {pts} pts"
        self.update_turn_ui()   # re-render table with dimming applied

    def _on_roller_hidden(self):
        """
        Called when the player closes the roller window mid-turn (instead of
        using the Done button).  Re-enable the Open Roller button so they can
        get it back without losing their roll state.
        """
        if hasattr(self, "open_roller_btn"):
            self.open_roller_btn.setEnabled(True)
        # If they hadn't confirmed dice yet, unlock the table too so they're
        # not stuck — they can reopen and finish rolling, or the button is
        # there to bring the window back.
        if self._roller_dice is None:
            self.table.setEnabled(False)   # still waiting for a roll — keep locked
            self.turn_label.setText(
                f"🎲 Roller closed — click 'Open Roller' to continue rolling."
            )
            self.turn_label.setStyleSheet(
                f"color: {CLR_INVALID}; border: 2px solid {CLR_INVALID}44; "
                f"padding: 6px; font-size: 11px;"
            )
            self.turn_label.setVisible(True)

    def apply_roller_theme(self, theme_name: str):
        """
        Restyle the scorecard to match the roller's chosen theme.
        Derives accent / background colours from _ROLLER_THEMES and rebuilds
        the window stylesheet, then triggers a full table repaint.
        """
        th = _ROLLER_THEMES.get(theme_name)
        if th is None:
            return

        bg     = th["bg"]
        accent = th["accent"]
        start  = th["bar_start"]
        end    = th["bar_end"]

        # Derive supporting colours from the theme accent
        # Table and unclaimed cells are darkened versions of the background
        import colorsys

        def _darken(hex_color: str, factor: float) -> str:
            hex_color = hex_color.lstrip("#")
            r, g, b = (int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v * factor)
            return "#{:02x}{:02x}{:02x}".format(int(r2*255), int(g2*255), int(b2*255))

        table_bg    = _darken(bg, 1.15) if bg != "#1a1a1a" else "#1e1e1e"
        unclaimed   = _darken(bg, 1.40)
        active_unc  = _darken(bg, 1.65)
        total_bg    = _darken(bg, 0.70)
        header_bg   = _darken(bg, 1.25)

        stylesheet = f"""
            QMainWindow, QDialog, QWidget {{ background-color: {bg}; color: #F1F5F9; }}
            QTableWidget {{
                background-color: {table_bg}; color: #F1F5F9;
                gridline-color: {unclaimed}; border: 1px solid {unclaimed};
            }}
            QHeaderView::section {{
                background-color: {header_bg}; color: {accent};
                padding: 5px; border: 1px solid {unclaimed}; font-weight: bold;
            }}
            QComboBox, QLineEdit {{
                background-color: {unclaimed}; color: #F1F5F9;
                border: 1px solid {active_unc}; border-radius: 3px; padding: 2px;
            }}
            QComboBox::drop-down {{ border: none; background-color: {unclaimed}; }}
            QComboBox::down-arrow {{ width: 10px; height: 10px; }}
            QComboBox QAbstractItemView {{
                background-color: {table_bg}; color: #F1F5F9;
                border: 1px solid {active_unc};
                selection-background-color: {accent};
                selection-color: #000000; outline: none;
            }}
            QComboBox QAbstractItemView::item {{ padding: 4px 8px; min-height: 24px; }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {active_unc}; color: #F1F5F9;
            }}
            QPushButton {{
                background-color: {unclaimed}; color: #F1F5F9;
                border-radius: 4px; padding: 10px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {active_unc}; }}
            QCheckBox {{ color: #F1F5F9; }}
        """
        self.setStyleSheet(stylesheet)

        # Also update the application-level stylesheet so that QComboBox popup
        # windows (which are top-level and inherit app styles, not window styles)
        # use the correct theme accent instead of always defaulting to blue.
        app = QApplication.instance()
        if app is not None:
            app_stylesheet = f"""
                QMainWindow, QDialog, QWidget {{ background-color: {bg}; color: #F1F5F9; }}
                QTableWidget {{
                    background-color: {table_bg}; color: #F1F5F9;
                    gridline-color: {unclaimed}; border: 1px solid {unclaimed};
                }}
                QHeaderView::section {{
                    background-color: {header_bg}; color: {accent};
                    padding: 5px; border: 1px solid {unclaimed}; font-weight: bold;
                }}
                QComboBox, QLineEdit {{
                    background-color: {unclaimed}; color: #F1F5F9;
                    border: 1px solid {active_unc}; border-radius: 3px; padding: 2px;
                }}
                QComboBox::drop-down {{ border: none; background-color: {unclaimed}; }}
                QComboBox::down-arrow {{ width: 10px; height: 10px; }}
                QComboBox QAbstractItemView {{
                    background-color: {table_bg};
                    color: #F1F5F9;
                    border: 1px solid {active_unc};
                    selection-background-color: {accent};
                    selection-color: #000000;
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{ padding: 4px 8px; min-height: 24px; }}
                QComboBox QAbstractItemView::item:hover {{
                    background-color: {active_unc}; color: #F1F5F9;
                }}
                QPushButton {{
                    background-color: {unclaimed}; color: #F1F5F9;
                    border-radius: 4px; padding: 10px; font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {active_unc}; }}
                QCheckBox {{ color: #F1F5F9; }}
            """
            app.setStyleSheet(app_stylesheet)

        # Cache derived colours so update_turn_ui can use them for dropdowns
        self._theme_accent    = accent
        self._theme_unclaimed = unclaimed
        self._theme_active    = active_unc
        self._theme_bg        = bg
        self._theme_table_bg  = table_bg

        # Restyle the Open Roller button to use the theme gradient
        if hasattr(self, "open_roller_btn"):
            self.open_roller_btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {start},stop:1 {end}); color: white; border-radius: 4px;"
                f"padding: 10px; font-weight: bold; }}"
                f"QPushButton:hover {{ opacity: 0.85; }}"
            )

        # Restyle the turn banner accent colour
        self.turn_timer_label.setStyleSheet(f"color: {accent}; padding: 2px 8px;")

        # Full table repaint so cell colours pick up the new palette
        self.update_turn_ui()

    def _on_scorecard_theme_changed(self, theme_name: str):
        """Theme picker in the scorecard drives both the scorecard and the roller."""
        self.apply_roller_theme(theme_name)
        if self._roller is not None:
            self._roller._set_theme(theme_name)

    # ----------------------------------------------------------- clock ------
    def _tick_clock(self):
        ms  = self._elapsed.elapsed()
        s, m, h = (ms // 1000) % 60, (ms // 60000) % 60, ms // 3600000
        self.timer_label.setText(
            f"⏱  {h:02d}:{m:02d}:{s:02d}" if h > 0 else f"⏱  {m:02d}:{s:02d}"
        )
        tms = self._turn_elapsed.elapsed()
        ts, tm = (tms // 1000) % 60, (tms // 60000) % 60
        color = "#F87171" if tms >= 120000 else "#F97316" if tms >= 60000 else CLR_ACTIVE_TURN
        self.turn_timer_label.setStyleSheet(f"color: {color}; padding: 2px 8px;")
        self.turn_timer_label.setText(f"🎲  {tm:02d}:{ts:02d}")

    def closeEvent(self, event):
        if hasattr(self, '_clock'): self._clock.stop()
        if hasattr(self, 'loop') and self.loop.isRunning(): self.loop.quit()
        if self._roller:
            # Disconnect the hidden callback so hiding doesn't fire _on_roller_hidden
            # then destroy the window for real.
            self._roller.on_window_hidden = lambda: None
            self._roller.close()
        event.accept()

    def show_rules(self):
        RulesDialog().exec()

    # --------------------------------------------------------- board --------
    def setup_board(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = QTableWidgetItem("-")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, "unclaimed")
                if r in CALCULATED_ROWS:
                    item.setText("0"); item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(QColor(self._theme_bg))
                    item.setForeground(QBrush(QColor(self._theme_accent)))
                elif r in UPPER_SECTION:
                    self.add_dropdown(r, c, ["-", "0", "1", "2", "3", "4", "5"])
                elif r == 15:
                    self.setup_yahtzee_bonus_cell(r, c); continue
                elif r in FIXED_SCORE_ROWS:
                    self.add_dropdown(r, c, ["-", str(FIXED_SCORE_ROWS[r]), "0"])
                elif r in [9, 10, 16]:
                    self.add_dropdown(r, c, ["-", "0"] + [str(i) for i in range(5, 31)])
                else:
                    item.setBackground(QColor(self._theme_unclaimed))
                self.table.setItem(r, c, item)
        self.table.blockSignals(False)

    def setup_yahtzee_bonus_cell(self, r, c):
        container = QWidget()
        lay       = QHBoxLayout(container); lay.setContentsMargins(2, 2, 2, 2)
        lbl = QLabel("0"); btn = QPushButton("+")
        btn.setFixedSize(25, 25)
        btn.clicked.connect(lambda _, col=c: self.increment_yahtzee_bonus(col))
        lay.addWidget(lbl); lay.addWidget(btn)
        self.table.setCellWidget(r, c, container)
        item = QTableWidgetItem("0")
        item.setData(Qt.ItemDataRole.UserRole, "bonus_row")
        self.table.setItem(r, c, item)

    def add_dropdown(self, r, c, options):
        btn = ScoreButton()
        btn.addItems(options)
        btn.setProperty("row", r); btn.setProperty("col", c)
        btn.set_theme_colors(self._theme_accent, self._theme_table_bg, self._theme_active)
        btn.connect_change(self.handle_dropdown)
        self.table.setCellWidget(r, c, btn)

    def _update_upper_dropdowns(self, c):
        is_active = (c == self.current_turn_index)
        for r in UPPER_SECTION:
            combo = self.table.cellWidget(r, c)
            if not combo or not isinstance(combo, ScoreButton): continue
            if self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "claimed": continue
            self._is_updating = True
            current = combo.currentText(); combo.clear()
            if (is_active and self.joker_active
                    and self.use_digital_roller and self._roller_dice is not None):
                # Joker + digital roller: offer exact count for this face (always 5),
                # or 0 if it's not the matching face (shouldn't happen per priority,
                # but guard for completeness)
                face  = r + 1
                count = Counter(self._roller_dice)[face]
                combo.addItems(["-", str(count)] if count > 0 else ["-", "0"])
            elif is_active and self.joker_active:
                combo.addItems(["-", "5", "0"])
            elif (is_active and self.use_digital_roller
                  and self._roller_dice is not None):
                face  = r + 1
                count = Counter(self._roller_dice)[face]
                if count > 0:
                    combo.addItems(["-", str(count)])
                else:
                    combo.addItems(["-", "0"])
            else:
                combo.addItems(["-", "0", "1", "2", "3", "4", "5"])
            idx = combo.findText(current)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            self._is_updating = False

    def _update_lower_dropdowns(self, c):
        """
        When roller dice are confirmed, restrict rows 9–14 and 16 to only the
        options valid for this roll.  Non-qualifying rows show [-, 0] only
        (red tint applied by the cell loop) so the player can still burn them.
        Restores normal options for physical dice / no roll yet / claimed cell.
        """
        is_active = (c == self.current_turn_index)
        lock_rows = {9, 10, 11, 12, 13, 14, 16}
        for r in lock_rows:
            combo = self.table.cellWidget(r, c)
            if not combo or not isinstance(combo, ScoreButton): continue
            if self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "claimed": continue
            self._is_updating = True
            current = combo.currentText(); combo.clear()
            if (is_active and self.use_digital_roller
                    and self._roller_dice is not None
                    and self.joker_active):
                # Joker + digital roller: dice are five-of-a-kind.
                # Per Joker rules, lower boxes may be used at full value.
                # Compute which lower boxes are available under Joker priority.
                total     = sum(self._roller_dice)
                joker_face = self._roller_dice[0]  # all five are the same
                # Matching upper box status
                upper_r   = joker_face - 1   # row index for matching upper
                upper_claimed = (
                    self.table.item(upper_r, c).data(Qt.ItemDataRole.UserRole) == "claimed"
                    if self.table.item(upper_r, c) else False
                )
                # Lower boxes are only scoreable if matching upper is already claimed
                if upper_claimed:
                    fixed = FIXED_SCORE_ROWS.get(r)
                    combo.addItems(["-", str(fixed)] if fixed else ["-", str(total)])
                else:
                    # Matching upper is open — player must score there first (Joker step 1)
                    # Lower boxes show 0 only (disabled by Joker dimming in cell loop)
                    combo.addItems(["-", "0"])
            elif (is_active and self.use_digital_roller
                    and self._roller_dice is not None
                    and not self.joker_active):
                total     = sum(self._roller_dice)
                counts    = Counter(self._roller_dice)
                max_count = max(counts.values())
                uniq      = sorted(set(self._roller_dice))

                # Full House (row 11): exactly 3+2
                if r == 11:
                    vals = sorted(counts.values(), reverse=True)
                    qualifies = (vals[0] == 3 and len(vals) > 1 and vals[1] == 2)

                # Small Straight (row 12): any 4 consecutive values present
                elif r == 12:
                    qualifies = any(
                        all(s in uniq for s in seq)
                        for seq in [(1,2,3,4), (2,3,4,5), (3,4,5,6)]
                    )

                # Large Straight (row 13): all 5 consecutive
                elif r == 13:
                    qualifies = uniq in [[1,2,3,4,5], [2,3,4,5,6]]

                # Yahtzii (row 14): five of a kind
                elif r == 14:
                    qualifies = (max_count == 5)

                # 3 of a Kind (row 9), 4 of a Kind (row 10), Chance (row 16)
                elif r == 9:
                    qualifies = (max_count >= 3)
                elif r == 10:
                    qualifies = (max_count >= 4)
                else:  # row 16 — Chance always qualifies
                    qualifies = True

                if qualifies:
                    fixed = FIXED_SCORE_ROWS.get(r)
                    combo.addItems(["-", str(fixed)] if fixed else ["-", str(total)])
                else:
                    combo.addItems(["-", "0"])
            else:
                # Restore defaults per row type
                if r in FIXED_SCORE_ROWS:
                    combo.addItems(["-", str(FIXED_SCORE_ROWS[r]), "0"])
                else:
                    combo.addItems(["-", "0"] + [str(i) for i in range(5, 31)])
            idx = combo.findText(current)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            self._is_updating = False

    # --------------------------------------------------------- scoring ------
    def _update_streak(self, c, score):
        if score > 0:
            if self._streak_player == self.players[c]:
                self._streak_count += 1
            else:
                self._streak_player = self.players[c]
                self._streak_count  = 1
        else:
            if self._streak_player == self.players[c]:
                self._streak_player = None
                self._streak_count  = 0

    def handle_dropdown(self, index, btn=None):
        if self._is_updating: return
        combo = btn if btn is not None else self.sender()
        if combo is None: return
        r, c  = combo.property("row"), combo.property("col")
        self._is_updating = True
        item   = self.table.item(r, c)
        status = item.data(Qt.ItemDataRole.UserRole)

        if combo.currentText() == "-":
            if status == "claimed":
                self._last_unclaimed_name = ROW_LABELS[r]
                item.setData(Qt.ItemDataRole.UserRole, "unclaimed")
                item.setText("-")
                self._correction_pending = True
                self.recalc(c); self.update_turn_ui()
            self._is_updating = False
            return

        old_val = item.text()
        score   = (int(combo.currentText()) * (r + 1) if r in UPPER_SECTION
                   else int(combo.currentText()))
        item.setText(str(score)); item.setData(Qt.ItemDataRole.UserRole, "claimed")

        if status == "unclaimed" and self._correction_pending:
            self._correction_pending = False
            self._correction_replaced_msg = (
                f"✔  {self._last_unclaimed_name} replaced by {ROW_LABELS[r]} "
                f"— now score your current turn"
            )
            self.recalc(c); self.update_turn_ui()
        elif status == "unclaimed":
            self._correction_replaced_msg = ""
            roll_info = ""
            if self.use_digital_roller and self._roller_dice is not None:
                faces = "  ".join(str(d) for d in self._roller_dice)
                roll_info = f"  [{faces}] →"
            self._last_score_msg = (
                f"Last score: {self.players[c]}{roll_info} {ROW_LABELS[r]}  {score} pts"
            )
            # Update the roller history so it shows the actual category scored
            if self.use_digital_roller and self._roller is not None:
                self._roller.update_last_history_label(ROW_LABELS[r], score)
            self._update_streak(c, score)
            self.recalc(c); self.advance_to_next_player()
        else:
            self._correction_replaced_msg = (
                f"✔  {ROW_LABELS[r]} changed from {old_val} to {score} pts "
                f"— now score your current turn"
            )
            self.recalc(c); self.update_turn_ui()

        self._is_updating = False

    def increment_yahtzee_bonus(self, c):
        if self.table.item(14, c).text() != "50":
            QMessageBox.warning(
                self, "Rule Violation",
                "Yahtzii Bonus requires a 50 in the Yahtzii box!"
            )
            return
        item = self.table.item(15, c)
        val  = int(item.text()) + 1
        item.setText(str(val))
        self.table.cellWidget(15, c).findChild(QLabel).setText(str(val))
        self._last_score_msg = f"Last score: {self.players[c]} → Yahtzii Bonus  +100 pts"
        self.joker_active = True
        self.recalc(c); self.update_turn_ui()

    def advance_to_next_player(self):
        self.joker_active             = False
        self._correction_pending      = False
        self._last_unclaimed_name     = ""
        self._correction_replaced_msg = ""
        self._roller_dice             = None   # clear roll — next player starts fresh
        if hasattr(self, '_turn_elapsed'):
            self._turn_elapsed.restart()
            self.turn_timer_label.setStyleSheet(
                f"color: {CLR_ACTIVE_TURN}; padding: 2px 8px;"
            )
        total = len(self.players)
        for _ in range(total):
            self.current_turn_index = (self.current_turn_index + 1) % total
            if self.player_has_turns_left(self.current_turn_index):
                self.update_turn_ui()
                if self.use_digital_roller:
                    self._open_roller_for_current_player()
                return
        self.check_game_over()

    def player_has_turns_left(self, c):
        return any(
            self.table.item(r, c).data(Qt.ItemDataRole.UserRole) == "unclaimed"
            for r in PRIMARY_CATEGORIES
        )

    def recalc(self, c):
        u_sum = sum(int(self.table.item(r, c).text()) for r in range(6)
                    if self.table.item(r, c).text().isdigit())
        self.table.item(6, c).setText(str(u_sum))
        bonus = 35 if u_sum >= 63 else 0
        self.table.item(7, c).setText(str(bonus))
        self.table.item(8, c).setText(str(u_sum + bonus))
        l_sum = sum(int(self.table.item(r, c).text()) for r in [9,10,11,12,13,14,16]
                    if self.table.item(r, c).text().isdigit())
        y_bonus = int(self.table.item(15, c).text()) * 100
        self.table.item(17, c).setText(str(l_sum + y_bonus))
        self.table.item(18, c).setText(str(u_sum + bonus + l_sum + y_bonus))

    # ------------------------------------------------------ UI updates ------
    def _valid_rows_for_dice(self, dice: list) -> set:
        """
        Return the set of PRIMARY_CATEGORIES row indices that are genuinely
        scoreable (non-zero) with this specific roll.  Rows not in this set
        should be dimmed — the player may still score a zero there, but they
        are visually de-emphasised.
        """
        counts = Counter(dice)
        total  = sum(dice)
        vals   = sorted(counts.values(), reverse=True)
        uniq   = sorted(set(dice))
        valid  = set()

        # Upper section rows 0-5: valid if at least one die matches face value
        for r in range(6):
            face = r + 1
            if counts[face] > 0:
                valid.add(r)

        # 3 of a Kind (row 9)
        if vals[0] >= 3:
            valid.add(9)

        # 4 of a Kind (row 10)
        if vals[0] >= 4:
            valid.add(10)

        # Full House (row 11)
        if vals[0] == 3 and len(vals) > 1 and vals[1] == 2:
            valid.add(11)

        # Small Straight (row 12): any 4 sequential values present
        for seq in [(1,2,3,4), (2,3,4,5), (3,4,5,6)]:
            if all(s in uniq for s in seq):
                valid.add(12)
                break

        # Large Straight (row 13): all 5 sequential
        if uniq in [[1,2,3,4,5], [2,3,4,5,6]]:
            valid.add(13)

        # Yahtzii (row 14)
        if vals[0] == 5:
            valid.add(14)

        # Chance (row 16) — always valid
        valid.add(16)

        return valid

    def update_turn_ui(self):
        curr      = self.current_turn_index
        CLR_PEND  = "#93C5FD"

        if self._roller_active:
            pass   # banner already set by _open_roller_for_current_player
        elif self.joker_active:
            if self.use_digital_roller and self._roller_dice is not None:
                # Tell the player exactly what they rolled and what the priority is
                joker_face  = self._roller_dice[0]
                face_name   = ["Ones","Twos","Threes","Fours","Fives","Sixes"][joker_face - 1]
                upper_r     = joker_face - 1
                upper_item  = self.table.item(upper_r, self.current_turn_index)
                upper_claimed = (upper_item and
                                 upper_item.data(Qt.ItemDataRole.UserRole) == "claimed")
                if not upper_claimed:
                    joker_msg = (
                        f"🃏 Joker — Five {face_name}!  "
                        f"① {face_name} box is open — you must score there."
                    )
                else:
                    joker_msg = (
                        f"🃏 Joker — Five {face_name}!  "
                        f"① {face_name} already claimed.  "
                        f"② Score any open Lower box at full value."
                    )
            else:
                joker_msg = (
                    "🃏 Joker Rules Active  —  "
                    "① Score matching Upper box if open  "
                    "② Otherwise score any open Lower box  "
                    "③ If all Lower full, take 0 in any Upper box"
                )
            self.turn_label.setText(joker_msg)
            self.turn_label.setStyleSheet(
                f"color: #3B82F6; border: 2px solid {CLR_ACCENT}; "
                f"padding: 6px; font-size: 11px;"
            )
            self.turn_label.setVisible(True)
        elif self._correction_replaced_msg:
            self.turn_label.setText(self._correction_replaced_msg)
            self.turn_label.setStyleSheet(
                f"color: #34D399; border: 2px solid #34D399; padding: 6px; font-size: 11px;"
            )
            self.turn_label.setVisible(True)
        elif self._correction_pending:
            self.turn_label.setText(
                f"⚠️  {self._last_unclaimed_name} unclaimed — fill any box to replace it, "
                f"then score your turn"
            )
            self.turn_label.setStyleSheet(
                f"color: {CLR_PEND}; border: 2px solid {CLR_PEND}; "
                f"padding: 6px; font-size: 11px;"
            )
            self.turn_label.setVisible(True)
        else:
            self.turn_label.setVisible(False)

        for c, name in enumerate(self.players):
            if len(self.players) == 1:
                self.table.setHorizontalHeaderItem(c, QTableWidgetItem(name))
            else:
                self.table.setHorizontalHeaderItem(
                    c, QTableWidgetItem(f"▶  {name}" if c == curr else name)
                )

        UPPER_TT       = "① Joker: score here first if this matches your five-of-a-kind number."
        LOWER_TT       = "② Joker: score here if your matching Upper box is already claimed."
        ROLLER_ZERO_TT = "No score with this roll — select 0 to burn this category."
        JOKER_BLOCKED_TT = "① Joker: your matching Upper box is open — score there first."

        # Pre-compute valid rows for the active player's confirmed roll (if any)
        roller_valid = (
            self._valid_rows_for_dice(self._roller_dice)
            if self.use_digital_roller and self._roller_dice is not None
            else None
        )

        # When Joker + roller are both active, determine which rows are
        # scoreable under Joker priority rules given the specific dice.
        joker_roller_state = None   # None | "must_upper" | "use_lower"
        joker_upper_r      = None
        if (self.joker_active and self.use_digital_roller
                and self._roller_dice is not None):
            joker_face    = self._roller_dice[0]
            joker_upper_r = joker_face - 1
            upper_item    = self.table.item(joker_upper_r, curr)
            if upper_item and upper_item.data(Qt.ItemDataRole.UserRole) != "claimed":
                joker_roller_state = "must_upper"   # step ①: upper box is open
            else:
                joker_roller_state = "use_lower"    # step ②: use any lower box

        # Red-tint background for zero-only cells
        CLR_ZERO_BG  = "#2D0F0F"   # dark red background
        CLR_ZERO_FG  = "#F87171"   # red text

        for c in range(self.table.columnCount()):
            is_active = (c == curr)
            self.update_yahtzee_bonus_state(c)
            self._update_upper_dropdowns(c)
            self._update_lower_dropdowns(c)
            for r in range(self.table.rowCount()):
                item   = self.table.item(r, c)
                widget = self.table.cellWidget(r, c)
                if not item or r in CALCULATED_ROWS: continue
                status = item.data(Qt.ItemDataRole.UserRole)

                # Base background
                bg = (self._theme_table_bg if status == "claimed"
                      else self._theme_active if is_active else self._theme_unclaimed)

                roller_zero    = False
                joker_blocked  = False

                if is_active and status == "unclaimed":
                    if joker_roller_state == "must_upper":
                        # Step ①: only the matching upper row is valid
                        if r == joker_upper_r:
                            bg = self._theme_active   # highlight it
                        elif r in PRIMARY_CATEGORIES:
                            bg = CLR_DISABLED
                            joker_blocked = True

                    elif joker_roller_state == "use_lower":
                        # Step ②: any open lower box is valid; upper is dimmed
                        if r in LOWER_SECTION_PRIMARY:
                            bg = self._theme_active
                        elif r in UPPER_SECTION:
                            bg = CLR_DISABLED
                            joker_blocked = True
                        elif r not in LOWER_SECTION_PRIMARY and r in PRIMARY_CATEGORIES:
                            bg = CLR_DISABLED
                            joker_blocked = True

                    elif self.joker_active:
                        # Plain Joker (no roller dice): existing dim logic
                        if r not in LOWER_SECTION_PRIMARY and r not in UPPER_SECTION:
                            bg = CLR_DISABLED

                    elif roller_valid is not None:
                        # Pure roller (no Joker): red tint for zero-only rows
                        if r in PRIMARY_CATEGORIES and r not in roller_valid:
                            bg = CLR_ZERO_BG
                            roller_zero = True

                item.setBackground(QColor(bg))
                fg = (CLR_ZERO_FG  if roller_zero
                      else "#4A5568" if joker_blocked
                      else CLR_CLAIMED_TEXT if status == "claimed"
                      else "#F1F5F9")
                item.setForeground(QBrush(QColor(fg)))

                # Tooltips
                if is_active and status == "unclaimed":
                    if joker_roller_state == "must_upper" and r == joker_upper_r:
                        tt = UPPER_TT
                    elif joker_roller_state == "must_upper" and joker_blocked:
                        tt = JOKER_BLOCKED_TT
                    elif joker_roller_state == "use_lower" and r in LOWER_SECTION_PRIMARY:
                        tt = LOWER_TT
                    elif joker_roller_state == "use_lower" and joker_blocked:
                        tt = JOKER_BLOCKED_TT
                    elif self.joker_active and not joker_roller_state:
                        tt = (UPPER_TT if r in UPPER_SECTION
                              else LOWER_TT if r in LOWER_SECTION_PRIMARY else "")
                    elif roller_zero:
                        tt = ROLLER_ZERO_TT
                    else:
                        tt = ""
                else:
                    tt = ""
                item.setToolTip(tt)
                if widget: widget.setToolTip(tt)

                if widget and isinstance(widget, ScoreButton):
                    txt = (CLR_ZERO_FG  if roller_zero
                           else "#4A5568"  if joker_blocked
                           else CLR_CLAIMED_TEXT if status == "claimed"
                           else "white")
                    widget.set_theme_colors(
                        self._theme_accent,
                        self._theme_table_bg,
                        self._theme_active,
                    )
                    widget.apply_cell_style(bg, txt)
                    widget.setEnabled(is_active and not joker_blocked)

        self.update_status_bar()

    def update_yahtzee_bonus_state(self, c):
        widget = self.table.cellWidget(15, c)
        if not widget: return
        can_bonus = self.table.item(14, c).text() == "50" and not self.joker_active
        widget.setEnabled(can_bonus and c == self.current_turn_index)
        widget.setStyleSheet(
            f"background-color: {CLR_ACCENT if can_bonus else CLR_DISABLED};"
        )

    # -------------------------------------------------- status bar ----------
    def _load_alltime_high(self):
        try:
            if os.path.exists("yahtzee_highscores.json"):
                with open("yahtzee_highscores.json") as f:
                    data = json.load(f)
                if data:
                    t = data[0]
                    self._sb_data['alltime'] = (
                        f"🏅 All-time: {t['name']} {t['score']} pts ({t['date']})"
                    )
                    return
        except Exception:
            pass
        self._sb_data['alltime'] = "🏅 All-time: —"

    def _render_status_bar(self):
        d = self._sb_data
        def c3(text, color, align="left", bold=False):
            w = "font-weight:bold;" if bold else ""
            return (f"<td width='33%' style='color:{color};{w}text-align:{align};"
                    f"white-space:nowrap;padding:0 4px;'>{text}</td>")
        def c4(text, color, align="left", bold=False):
            w = "font-weight:bold;" if bold else ""
            return (f"<td width='25%' style='color:{color};{w}text-align:{align};"
                    f"white-space:nowrap;padding:0 4px;'>{text}</td>")
        self._sb_row1.setText(
            "<table width='100%' cellspacing='0' cellpadding='0'><tr>"
            + c3(d['leader'], CLR_ACTIVE_TURN, "left", bold=True)
            + c3(d['scores'], CLR_ACCENT,       "center")
            + c3(d['last'],   CLR_CLAIMED_TEXT, "right")
            + "</tr></table>"
        )
        self._sb_row2.setText(
            "<table width='100%' cellspacing='0' cellpadding='0'><tr>"
            + c4(d['upper'],   d['upper_color'], "left")
            + c4(d['streak'],  "#F97316",        "center")
            + c4(d['best'],    CLR_CLAIMED_TEXT, "center")
            + c4(d['alltime'], "#94A3B8",        "right")
            + "</tr></table>"
        )

    def update_status_bar(self):
        if not hasattr(self, '_sb_data'): return
        totals = [int(self.table.item(18, c).text()) for c in range(len(self.players))]
        curr   = self.current_turn_index
        solo   = (len(self.players) == 1)
        d      = self._sb_data

        if solo:
            d['leader'] = f"🎲 {self.players[0]}  —  {totals[0]} pts"
            d['scores'] = ""
        else:
            best_c = totals.index(max(totals))
            d['leader'] = f"🏆 {self.players[best_c]} leading ({totals[best_c]} pts)"
            d['scores'] = "  ".join(
                f"{self.players[c]}: {totals[c]}" for c in range(len(self.players))
            )

        d['last'] = getattr(self, '_last_score_msg', "")

        u_sum = sum(int(self.table.item(r, curr).text()) for r in range(6)
                    if self.table.item(r, curr).text().isdigit())
        if u_sum >= 63:
            d['upper']       = f"Upper: {self.players[curr]} {u_sum}/63 ✓ Bonus earned!"
            d['upper_color'] = CLR_ACCENT
        else:
            d['upper']       = f"Upper: {self.players[curr]} {u_sum}/63 — {63 - u_sum} needed"
            d['upper_color'] = '#94A3B8'

        best_score, best_who, best_cat = 0, "", ""
        for c in range(len(self.players)):
            for r in PRIMARY_CATEGORIES:
                item = self.table.item(r, c)
                if item and item.data(Qt.ItemDataRole.UserRole) == "claimed":
                    val = int(item.text()) if item.text().lstrip('-').isdigit() else 0
                    if val > best_score:
                        best_score, best_who, best_cat = val, self.players[c], ROW_LABELS[r]
        d['best'] = (f"🎯 Best: {best_who} → {best_cat} ({best_score} pts)"
                     if best_who else "🎯 Best: —")

        if solo:
            # Replace streak slot with categories remaining count
            remaining = sum(
                1 for r in PRIMARY_CATEGORIES
                if self.table.item(r, 0) and
                self.table.item(r, 0).data(Qt.ItemDataRole.UserRole) == "unclaimed"
            )
            d['streak'] = f"📋 {remaining} categor{'y' if remaining == 1 else 'ies'} left"
        else:
            sp, sn = self._streak_player, self._streak_count
            if sp and sn >= 2:
                d['streak'] = f"{'🔥' * min(sn, 3)} {sp}: {sn}-turn streak"
            else:
                st = sorted(enumerate(totals), key=lambda x: x[1], reverse=True)
                if len(st) >= 2:
                    li, ls = st[0]; si, ss = st[1]
                    gap = ls - ss
                    d['streak'] = (f"📊 {self.players[li]} & {self.players[si]} tied!"
                                   if gap == 0 else
                                   f"📊 {self.players[si]} trails {self.players[li]} by {gap} pts")
                else:
                    d['streak'] = ""
        self._render_status_bar()

    # ------------------------------------------------ game over / save ------
    def check_game_over(self):
        for c in range(self.table.columnCount()):
            if self.player_has_turns_left(c): return
        scores = sorted(
            [(self.players[i], int(self.table.item(18, i).text()))
             for i in range(len(self.players))],
            key=lambda x: x[1], reverse=True
        )
        self.save_high_score(scores[0][0], scores[0][1])
        dlg    = GameOverDialog(scores, self); dlg.exec()
        choice = dlg.result_choice
        self.play_again_requested = choice in (
            GameOverDialog.SAME_ORDER, GameOverDialog.ROLL_ORDER, GameOverDialog.NEW_GAME
        )
        self.roll_for_order = (choice == GameOverDialog.ROLL_ORDER)
        self.new_game       = (choice == GameOverDialog.NEW_GAME)
        self.close()

    def save_high_score(self, name, score):
        filename    = "yahtzee_highscores.json"
        scores_data = []
        if os.path.exists(filename):
            try:
                with open(filename) as f: scores_data = json.load(f)
            except json.JSONDecodeError: pass
        scores_data.append({
            "name": name, "score": score,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        scores_data = sorted(scores_data, key=lambda x: x["score"], reverse=True)[:10]
        with open(filename, "w") as f:
            json.dump(scores_data, f, indent=4)
        self._load_alltime_high()

    def show_high_scores(self):
        filename = "yahtzee_highscores.json"
        dialog   = QDialog(self)
        dialog.setWindowTitle("Top 10 High Scores")
        dialog.resize(350, 400)
        dialog.setStyleSheet(DARK_STYLESHEET)
        layout = QVBoxLayout(dialog)
        if not os.path.exists(filename):
            msg = QLabel("No high scores recorded yet.")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(msg)
        else:
            try:
                with open(filename) as f: data = json.load(f)
                tbl = QTableWidget(len(data), 3)
                tbl.setHorizontalHeaderLabels(["Rank", "Player", "Score"])
                tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                for r, row_data in enumerate(data):
                    tbl.setItem(r, 0, QTableWidgetItem(f"#{r+1}"))
                    tbl.setItem(r, 1, QTableWidgetItem(row_data["name"]))
                    tbl.setItem(r, 2, QTableWidgetItem(str(row_data["score"])))
                layout.addWidget(tbl)
            except Exception as e:
                layout.addWidget(QLabel(f"Error: {e}"))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        dialog.exec()

    def reset(self):
        if QMessageBox.question(self, "Reset", "Clear?") == QMessageBox.StandardButton.Yes:
            self.current_turn_index = 0
            self._roller_dice       = None
            self.setup_board()
            if hasattr(self, '_elapsed'):      self._elapsed.restart()
            if hasattr(self, '_turn_elapsed'): self._turn_elapsed.restart()
            self.turn_timer_label.setStyleSheet(
                f"color: {CLR_ACTIVE_TURN}; padding: 2px 8px;"
            )
            self.update_turn_ui()
            if self.use_digital_roller:
                self._open_roller_for_current_player()


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)

    ordered_names    = None
    prefill_names    = None
    use_roller_carry = False
    theme_carry      = "Classic"

    while True:
        # --- Registration ---
        if ordered_names is None:
            setup = PlayerSetupDialog(prefill=prefill_names, initial_theme=theme_carry)
            prefill_names = None
            if not setup.exec():
                break
            names = [
                i.text().strip() or f"P{idx+1}"
                for idx, (_, i) in enumerate(setup.player_inputs)
            ]
            use_roller_carry = setup.use_digital_roller_enabled()
            theme_carry      = setup.selected_theme()
        else:
            names = ordered_names

        # --- Roll-off (skipped for single player) ---
        if len(names) > 1:
            rolloff = RollOffDialog(names)
            if not rolloff.exec():
                break
            ordered_names = rolloff.sorted_names
        else:
            ordered_names = names

        # --- Game ---
        w      = YahtzeeScorecard(ordered_names, use_digital_roller=use_roller_carry, initial_theme=theme_carry)
        w.loop = QEventLoop()
        w.show()
        if use_roller_carry:
            w._open_roller_for_current_player()
        w.loop.exec()

        if not getattr(w, 'play_again_requested', False):
            sys.exit(0)

        if getattr(w, 'new_game', False):
            prefill_names    = ordered_names
            ordered_names    = None
            use_roller_carry = False   # let them choose again at registration
            # theme_carry preserved so registration pre-selects the last theme
            continue

        if not getattr(w, 'roll_for_order', False) or len(ordered_names) == 1:
            # Same Order — skip registration and rolloff entirely
            w2_names = ordered_names
            while True:
                w2      = YahtzeeScorecard(w2_names, use_digital_roller=use_roller_carry, initial_theme=theme_carry)
                w2.loop = QEventLoop()
                w2.show()
                if use_roller_carry:
                    w2._open_roller_for_current_player()
                w2.loop.exec()

                if not getattr(w2, 'play_again_requested', False):
                    sys.exit(0)
                if getattr(w2, 'new_game', False):
                    prefill_names    = w2_names
                    ordered_names    = None
                    use_roller_carry = False
                    break
                if getattr(w2, 'roll_for_order', False):
                    ordered_names = w2_names
                    break
                # else same order again — keep inner loop running

        # Roll for Order path: ordered_names is set, outer loop goes back to rolloff

    sys.exit(0)
