"""
Custom graphical widgets for Desktop Audio Tuner & Equalizer:
- EQCurveWidget: Interactive spline frequency response curve with drag points and grid
- SpectrumWidget: 48-band dynamic spectrum analyzer with peak-hold decay
- RotaryDialWidget: Studio-style radial control knob with glowing LED arc
- EQBandSliderWidget: Precision vertical EQ slider with 0dB center detent
"""

import math
from typing import Callable, List, Optional, Tuple
import numpy as np
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QRadialGradient,
    QLinearGradient, QPainterPath, QMouseEvent
)
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy

EQ_FREQUENCIES = [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
EQ_LABELS = ["31Hz", "63Hz", "125Hz", "250Hz", "500Hz", "1kHz", "2kHz", "4kHz", "8kHz", "16kHz"]


class EQCurveWidget(QWidget):
    """
    Interactive frequency response curve display.
    Draws logarithmic grid (20 Hz - 20 kHz), 0dB reference line,
    filled spline frequency response curve, and draggable control points.
    """

    band_changed = pyqtSignal(int, float)  # (band_index, gain_db)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.bands = [0.0] * 10
        self.bass_boost = 0
        self.vocal_clarity = 0
        self.treble_air = 0
        self.preamp = 0.0
        self.bypass = False

        self.dragging_index: Optional[int] = None
        self.hover_index: Optional[int] = None
        self.setMouseTracking(True)

    def set_parameters(self, bands: List[float], bass_boost: int, vocal_clarity: int, treble_air: int, preamp: float, bypass: bool):
        self.bands = list(bands)
        self.bass_boost = bass_boost
        self.vocal_clarity = vocal_clarity
        self.treble_air = treble_air
        self.preamp = preamp
        self.bypass = bypass
        self.update()

    def _freq_to_x(self, freq: float, w: float) -> float:
        """Convert log frequency (20 Hz to 20 kHz) to widget X pixel."""
        log_min = math.log10(20.0)
        log_max = math.log10(20000.0)
        norm = (math.log10(max(20.0, min(20000.0, freq))) - log_min) / (log_max - log_min)
        return 36.0 + norm * (w - 56.0)

    def _x_to_freq(self, x: float, w: float) -> float:
        log_min = math.log10(20.0)
        log_max = math.log10(20000.0)
        norm = max(0.0, min(1.0, (x - 36.0) / (w - 56.0)))
        return 10.0 ** (log_min + norm * (log_max - log_min))

    def _gain_to_y(self, gain: float, h: float) -> float:
        """Convert gain (-15 dB to +15 dB) to widget Y pixel."""
        norm = (gain - (-15.0)) / 30.0  # 0.0 at -15dB, 1.0 at +15dB
        return h - 24.0 - norm * (h - 40.0)

    def _y_to_gain(self, y: float, h: float) -> float:
        norm = (h - 24.0 - y) / (h - 40.0)
        return max(-12.0, min(12.0, round(-15.0 + norm * 30.0, 1)))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = float(self.width())
        h = float(self.height())

        # 1. Dark Card Background
        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0.0, QColor(16, 21, 29))
        bg_grad.setColorAt(1.0, QColor(11, 15, 22))
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(QPen(QColor(36, 46, 62), 1.5))
        painter.drawRoundedRect(QRectF(6, 6, w - 12, h - 12), 10, 10)

        # 2. Decibel Horizontal Grid Lines (+12, +6, 0, -6, -12 dB)
        font_axis = QFont("Segoe UI", 7)
        painter.setFont(font_axis)

        for db in [12, 6, 0, -6, -12]:
            gy = self._gain_to_y(db, h)
            if db == 0:
                painter.setPen(QPen(QColor(88, 166, 255, 90), 1.5, Qt.DashLine))
            else:
                painter.setPen(QPen(QColor(36, 48, 66, 120), 1, Qt.DotLine))
            painter.drawLine(QPointF(32, gy), QPointF(w - 18, gy))

            # dB labels
            painter.setPen(QColor(100, 120, 150))
            painter.drawText(QRectF(4, gy - 6, 26, 12), Qt.AlignRight, f"{db:+d}" if db != 0 else "0")

        # 3. Frequency Vertical Grid Lines
        grid_freqs = [50, 100, 250, 500, 1000, 2000, 4000, 8000, 16000]
        for gf in grid_freqs:
            gx = self._freq_to_x(gf, w)
            painter.setPen(QPen(QColor(36, 48, 66, 90), 1, Qt.DotLine))
            painter.drawLine(QPointF(gx, 14), QPointF(gx, h - 20))

            lbl = f"{gf//1000}k" if gf >= 1000 else str(gf)
            painter.setPen(QColor(90, 110, 140))
            painter.drawText(QRectF(gx - 15, h - 18, 30, 12), Qt.AlignCenter, lbl)

        # 4. Generate & Draw Continuous Spline Curve
        n_eval = 250
        eval_freqs = np.logspace(np.log10(20), np.log10(20000), n_eval)

        if self.bypass:
            eval_gains = np.zeros(n_eval)
        else:
            log_iso = np.log10(EQ_FREQUENCIES)
            log_f = np.log10(eval_freqs)
            base_gains = np.interp(log_f, log_iso, self.bands)

            bb_gain = (self.bass_boost / 100.0) * 6.5
            bass_curve = bb_gain / (1.0 + (eval_freqs / 80.0) ** 2)

            vc_gain = (self.vocal_clarity / 100.0) * 5.0
            vocal_curve = vc_gain * np.exp(-0.5 * ((np.log2(eval_freqs / 2500.0)) / 0.8) ** 2)

            ta_gain = (self.treble_air / 100.0) * 5.0
            treble_curve = ta_gain * (1.0 / (1.0 + (10000.0 / np.maximum(1.0, eval_freqs)) ** 3))

            eval_gains = base_gains + bass_curve + vocal_curve + treble_curve

        pts = []
        for f, g in zip(eval_freqs, eval_gains):
            pts.append(QPointF(self._freq_to_x(f, w), self._gain_to_y(g, h)))

        curve_path = QPainterPath()
        if pts:
            curve_path.moveTo(pts[0])
            for pt in pts[1:]:
                curve_path.lineTo(pt)

        # Fill under curve
        fill_path = QPainterPath(curve_path)
        y_zero = self._gain_to_y(0.0, h)
        fill_path.lineTo(pts[-1].x(), y_zero)
        fill_path.lineTo(pts[0].x(), y_zero)
        fill_path.closeSubpath()

        curve_fill = QLinearGradient(0, 16, 0, h - 20)
        curve_fill.setColorAt(0.0, QColor(0, 229, 255, 60))
        curve_fill.setColorAt(0.5, QColor(0, 230, 118, 40))
        curve_fill.setColorAt(1.0, QColor(168, 85, 247, 10))
        painter.setBrush(QBrush(curve_fill))
        painter.setPen(Qt.NoPen)
        painter.drawPath(fill_path)

        # Draw Neon Glow Line
        glow_pen = QPen(QColor(0, 229, 255, 70), 5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(glow_pen)
        painter.drawPath(curve_path)

        # Crisp Center Line
        line_pen = QPen(QColor(0, 229, 255, 230) if not self.bypass else QColor(120, 140, 170), 2.0)
        painter.setPen(line_pen)
        painter.drawPath(curve_path)

        # 5. Draw 10 Interactive Control Points
        for i, (f, g) in enumerate(zip(EQ_FREQUENCIES, self.bands)):
            px = self._freq_to_x(f, w)
            py = self._gain_to_y(g, h)

            is_active = (i == self.dragging_index or i == self.hover_index)
            pt_radius = 6 if is_active else 4

            if is_active:
                painter.setBrush(QBrush(QColor(0, 255, 136)))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
            else:
                painter.setBrush(QBrush(QColor(24, 32, 46)))
                painter.setPen(QPen(QColor(0, 229, 255), 1.8))

            painter.drawEllipse(QPointF(px, py), pt_radius, pt_radius)

            # Draw tooltip on active point
            if is_active:
                tip_font = QFont("Segoe UI", 8, QFont.Bold)
                painter.setFont(tip_font)
                tip_text = f"{g:+.1f} dB"
                painter.setBrush(QBrush(QColor(10, 14, 20, 220)))
                painter.setPen(QPen(QColor(0, 255, 136), 1))
                t_rect = QRectF(px - 26, py - 24, 52, 18)
                painter.drawRoundedRect(t_rect, 4, 4)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(t_rect, Qt.AlignCenter, tip_text)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            w, h = float(self.width()), float(self.height())
            pos = event.pos()
            # Check closest point
            closest_idx = None
            min_dist = 20.0  # Hitbox radius
            for i, (f, g) in enumerate(zip(EQ_FREQUENCIES, self.bands)):
                px = self._freq_to_x(f, w)
                py = self._gain_to_y(g, h)
                dist = math.hypot(pos.x() - px, pos.y() - py)
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i

            if closest_idx is not None:
                self.dragging_index = closest_idx
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        w, h = float(self.width()), float(self.height())
        pos = event.pos()

        if self.dragging_index is not None:
            new_gain = self._y_to_gain(pos.y(), h)
            self.bands[self.dragging_index] = new_gain
            self.band_changed.emit(self.dragging_index, new_gain)
            self.update()
        else:
            # Check hover
            prev_hover = self.hover_index
            self.hover_index = None
            for i, (f, g) in enumerate(zip(EQ_FREQUENCIES, self.bands)):
                px = self._freq_to_x(f, w)
                py = self._gain_to_y(g, h)
                if math.hypot(pos.x() - px, pos.y() - py) < 14.0:
                    self.hover_index = i
                    break
            if prev_hover != self.hover_index:
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging_index = None
        self.update()


class SpectrumWidget(QWidget):
    """
    Real-time 48-band spectrum visualizer with peak hold & gravity decay.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.bars = np.zeros(48, dtype=np.float32)
        self.peaks = np.zeros(48, dtype=np.float32)
        self.peak_decay = 0.015

        self.decay_timer = QTimer(self)
        self.decay_timer.timeout.connect(self._decay_step)
        self.decay_timer.start(25)

    def set_spectrum(self, bars: np.ndarray):
        n = min(len(self.bars), len(bars))
        self.bars[:n] = bars[:n]
        self.peaks[:n] = np.maximum(self.peaks[:n], self.bars[:n])
        self.update()

    def _decay_step(self):
        self.bars *= 0.88
        self.peaks = np.maximum(0.0, self.peaks - self.peak_decay)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # Dark container
        painter.setBrush(QBrush(QColor(13, 17, 24)))
        painter.setPen(QPen(QColor(28, 36, 48), 1))
        painter.drawRoundedRect(QRectF(0, 0, w, h), 6, 6)

        n = len(self.bars)
        if n == 0 or w <= 0:
            return

        bar_spacing = 2.0
        bar_w = max(2.0, (w - 12.0 - (n - 1) * bar_spacing) / n)

        for i in range(n):
            bx = 6.0 + i * (bar_w + bar_spacing)
            val = float(self.bars[i])
            bar_h = max(2.0, val * (h - 10.0))
            by = h - 5.0 - bar_h

            # Dynamic Gradient (Cyan -> Emerald -> Purple)
            ratio = i / float(n)
            if ratio < 0.5:
                r = 0
                g = int(210 + 45 * (ratio / 0.5))
                b = int(255 * (1.0 - ratio / 0.5) + 120 * (ratio / 0.5))
            else:
                norm_r = (ratio - 0.5) / 0.5
                r = int(168 * norm_r)
                g = int(240 * (1.0 - norm_r) + 85 * norm_r)
                b = int(120 * (1.0 - norm_r) + 247 * norm_r)

            painter.setBrush(QBrush(QColor(r, g, b, 210)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 1.5, 1.5)

            # Peak marker
            peak_val = float(self.peaks[i])
            if peak_val > 0.05:
                py = h - 5.0 - peak_val * (h - 10.0)
                painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
                painter.drawLine(QPointF(bx, py), QPointF(bx + bar_w, py))


class RotaryDialWidget(QWidget):
    """
    Studio-style radial knob for Bass Boost, Vocal Clarity, Treble Air, Preamp.
    Supports vertical mouse dragging, mouse wheel, and double-click to reset.
    """

    value_changed = pyqtSignal(float)

    def __init__(self, title: str, min_val: float, max_val: float, default_val: float, suffix: str = "%", parent=None):
        super().__init__(parent)
        self.setFixedSize(92, 110)
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.default_val = default_val
        self.current_val = default_val
        self.suffix = suffix

        self.last_mouse_y = 0
        self.is_dragging = False

    def set_value(self, val: float):
        self.current_val = max(self.min_val, min(self.max_val, val))
        self.update()

    def get_value(self) -> float:
        return self.current_val

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_mouse_y = event.y()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging:
            dy = self.last_mouse_y - event.y()
            self.last_mouse_y = event.y()
            step = (self.max_val - self.min_val) / 100.0
            new_val = self.current_val + dy * step
            self.set_value(new_val)
            self.value_changed.emit(self.current_val)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.set_value(self.default_val)
        self.value_changed.emit(self.current_val)

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120.0
        step = (self.max_val - self.min_val) / 50.0
        self.set_value(self.current_val + delta * step)
        self.value_changed.emit(self.current_val)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = float(self.width())
        cx = w / 2.0
        cy = 44.0
        radius = 28.0

        # Title Label
        font_t = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_t)
        painter.setPen(QColor(140, 160, 190))
        painter.drawText(QRectF(0, 2, w, 16), Qt.AlignCenter, self.title)

        # Arc Background (from 225 deg to -45 deg, span 270 deg)
        arc_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.setPen(QPen(QColor(30, 40, 56), 4.5, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(arc_rect, int(-45 * 16), int(270 * 16))

        # Active Value Arc
        norm = (self.current_val - self.min_val) / (self.max_val - self.min_val)
        span_deg = int(norm * 270.0)

        arc_grad = QLinearGradient(0, cy - radius, 0, cy + radius)
        arc_grad.setColorAt(0.0, QColor(0, 229, 255))
        arc_grad.setColorAt(1.0, QColor(0, 230, 118))
        painter.setPen(QPen(QBrush(arc_grad), 4.5, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(arc_rect, int((225 - span_deg) * 16), int(span_deg * 16))

        # Inner Knob Metallic Body
        inner_r = radius - 6
        knob_grad = QRadialGradient(cx, cy, inner_r)
        knob_grad.setColorAt(0.0, QColor(36, 46, 62))
        knob_grad.setColorAt(0.8, QColor(20, 26, 36))
        knob_grad.setColorAt(1.0, QColor(14, 18, 26))
        painter.setBrush(QBrush(knob_grad))
        painter.setPen(QPen(QColor(48, 60, 80), 1.5))
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # Indicator Dot / Notch
        angle_deg = 225.0 - norm * 270.0
        angle_rad = math.radians(angle_deg)
        dot_r = inner_r - 4.5
        dx = cx + dot_r * math.cos(angle_rad)
        dy = cy - dot_r * math.sin(angle_rad)
        painter.setBrush(QBrush(QColor(0, 255, 136)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(dx, dy), 2.5, 2.5)

        # Bottom Numeric Value
        val_font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(val_font)
        painter.setPen(QColor(230, 240, 255))
        if self.suffix == "dB":
            v_text = f"{self.current_val:+.1f} {self.suffix}"
        else:
            v_text = f"{int(self.current_val)}{self.suffix}"
        painter.drawText(QRectF(0, 82, w, 20), Qt.AlignCenter, v_text)
