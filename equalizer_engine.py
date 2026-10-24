"""
Equalizer & Audio Optimization Engine.
Manages 10-band ISO EQ, enhancement DSP parameters (Bass Boost, Clarity, Treble Air, Preamp),
curated acoustic presets, and seamless real-time synchronization with Windows Equalizer APO.
"""

import json
import os
import shutil
import threading
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

# Standard 10-Band ISO Center Frequencies
EQ_FREQUENCIES = [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
EQ_BAND_LABELS = ["31 Hz", "63 Hz", "125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz", "8 kHz", "16 kHz"]
EQ_BAND_DESCRIPTIONS = [
    "超重低音 (Sub-bass)",
    "重低音打擊 (Punch)",
    "低頻溫暖度 (Warmth)",
    "低中頻厚實度 (Low Mid)",
    "中頻人聲主體 (Body)",
    "清晰度與人聲 (Clarity)",
    "穿透力與咬字 (Presence)",
    "臨場感與細節 (Detail)",
    "高頻光澤感 (Brilliance)",
    "空氣感與通透 (Air)"
]

# Standard Equalizer APO config path on Windows
APO_CONFIG_DIR = r"C:\Program Files\EqualizerAPO\config"
APO_CONFIG_FILE = os.path.join(APO_CONFIG_DIR, "config.txt")
APO_BACKUP_FILE = os.path.join(APO_CONFIG_DIR, "config.txt.tuner_backup")

# Presets Library
DEFAULT_PRESETS = {
    "⚖️ 平直原音直通 (Flat Reference)": {
        "description": "原始無修飾平直響應，監聽級真實聲音",
        "bands": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "bass_boost": 0,
        "vocal_clarity": 0,
        "treble_air": 0,
        "preamp": 0.0
    },
    "🎵 流行音樂 (Pop Music)": {
        "description": "飽滿動感的低頻節奏，人聲清晰靠前，高頻通透",
        "bands": [1.5, 2.5, 2.0, -0.5, -1.0, 1.0, 2.5, 2.0, 3.0, 2.5],
        "bass_boost": 15,
        "vocal_clarity": 20,
        "treble_air": 15,
        "preamp": -2.0
    },
    "🎸 搖滾金屬 (Rock & Metal)": {
        "description": "強勁大鼓打擊感，電吉他穿透力強，高鈸清脆不刺耳",
        "bands": [3.0, 4.5, 2.5, -1.0, 0.5, 1.5, 3.5, 4.0, 3.0, 2.0],
        "bass_boost": 25,
        "vocal_clarity": 15,
        "treble_air": 10,
        "preamp": -3.0
    },
    "🔊 極致重低音 (Bass Boost & EDM)": {
        "description": "深沉震動的極低頻，派對電音、Hip-Hop 震撼低音轟炸",
        "bands": [6.5, 5.5, 3.5, 1.0, -1.0, 0.0, 1.0, 1.5, 2.5, 3.5],
        "bass_boost": 45,
        "vocal_clarity": 10,
        "treble_air": 20,
        "preamp": -4.0
    },
    "🎙️ 人聲清晰 / Podcast (Vocal Clarity)": {
        "description": "消除環境低頻悶響，凸顯人聲咬字與演講對白，視訊會議推薦",
        "bands": [-4.0, -2.5, -1.0, 0.0, 1.5, 3.5, 4.5, 3.0, 1.5, 0.5],
        "bass_boost": 0,
        "vocal_clarity": 40,
        "treble_air": 10,
        "preamp": -1.5
    },
    "🎬 電影劇院震撼 (Cinema & 3D Surround)": {
        "description": "寬廣動態空間感，電影爆炸場景震撼，角色對白清晰分明",
        "bands": [5.0, 4.0, 2.0, -1.0, 0.0, 2.0, 3.0, 3.5, 4.0, 4.5],
        "bass_boost": 30,
        "vocal_clarity": 25,
        "treble_air": 25,
        "preamp": -3.5
    },
    "🎮 FPS 電競聽聲辨位 (Gaming Footsteps)": {
        "description": "壓抑轟炸低頻避免遮蔽腳步，強化 1.5k-4k 聽清腳步與切槍聲",
        "bands": [-3.5, -2.5, -1.0, 0.5, 1.5, 3.0, 5.0, 4.5, 2.5, 1.0],
        "bass_boost": 0,
        "vocal_clarity": 35,
        "treble_air": 15,
        "preamp": -2.0
    },
    "🎻 古典自然交響 (Classical Acoustic)": {
        "description": "純淨自然的管弦樂平衡，器樂層次分明，細膩優雅",
        "bands": [1.0, 1.5, 1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.0],
        "bass_boost": 5,
        "vocal_clarity": 10,
        "treble_air": 15,
        "preamp": -1.0
    },
    "🌙 深夜防爆音模式 (Night Mode)": {
        "description": "收斂過強低頻與刺耳高音，夜間看片追劇不吵醒家人",
        "bands": [-3.0, -2.0, -1.0, 0.5, 1.0, 1.5, 1.0, -0.5, -1.5, -2.0],
        "bass_boost": 0,
        "vocal_clarity": 15,
        "treble_air": 0,
        "preamp": -1.0
    },
    "🎧 耳機通透音場 (Headphone Soundstage)": {
        "description": "消除耳機頭中效應，擴大立體聲音場，使聽感更舒適寬廣",
        "bands": [2.0, 1.5, -0.5, -1.5, 0.0, 1.5, 2.5, 3.5, 4.0, 4.5],
        "bass_boost": 10,
        "vocal_clarity": 20,
        "treble_air": 30,
        "preamp": -2.5
    }
}


class EqualizerEngine:
    """
    Central state manager for EQ, Audio Enhancement dials, presets,
    and automatic Equalizer APO sync.
    """

    def __init__(self, custom_presets_file: Optional[str] = None):
        self.bands = [0.0] * 10
        self.bass_boost = 0        # 0 to 100 %
        self.vocal_clarity = 0     # 0 to 100 %
        self.treble_air = 0        # 0 to 100 %
        self.preamp = -2.0         # dB (-20 to +12)
        self.bypass = False        # True = bypass all processing

        # Presets storage
        if custom_presets_file is None:
            custom_presets_file = os.path.join(os.path.dirname(__file__), "custom_presets.json")
        self.presets_file = custom_presets_file
        self.custom_presets: Dict = {}
        self.load_custom_presets()

        # Equalizer APO integration status
        self.apo_installed = os.path.exists(APO_CONFIG_FILE)
        self.sync_apo_enabled = self.apo_installed
        self._apo_lock = threading.Lock()
        self._write_timer: Optional[threading.Timer] = None

        if self.apo_installed:
            self._backup_original_apo()

        # Apply default Pop preset on first start
        self.apply_preset("🎵 流行音樂 (Pop Music)")

    def _backup_original_apo(self):
        """Backup original config.txt once if not already backed up."""
        try:
            if os.path.exists(APO_CONFIG_FILE) and not os.path.exists(APO_BACKUP_FILE):
                shutil.copy2(APO_CONFIG_FILE, APO_BACKUP_FILE)
        except Exception as e:
            print(f"Failed to backup APO config: {e}")

    def set_band(self, index: int, gain_db: float):
        """Set gain of a specific frequency band (-12 to +12 dB)."""
        if 0 <= index < 10:
            self.bands[index] = max(-12.0, min(12.0, round(gain_db, 1)))
            self._trigger_apo_sync()

    def set_all_bands(self, gains: List[float]):
        """Set all 10 bands simultaneously."""
        for i in range(min(10, len(gains))):
            self.bands[i] = max(-12.0, min(12.0, round(gains[i], 1)))
        self._trigger_apo_sync()

    def set_bass_boost(self, val: int):
        """Set Bass Boost level (0 - 100)."""
        self.bass_boost = max(0, min(100, int(val)))
        self._trigger_apo_sync()

    def set_vocal_clarity(self, val: int):
        """Set Vocal Clarity level (0 - 100)."""
        self.vocal_clarity = max(0, min(100, int(val)))
        self._trigger_apo_sync()

    def set_treble_air(self, val: int):
        """Set Treble Air level (0 - 100)."""
        self.treble_air = max(0, min(100, int(val)))
        self._trigger_apo_sync()

    def set_preamp(self, gain_db: float):
        """Set Preamp Gain in dB (-20.0 to +12.0 dB)."""
        self.preamp = max(-20.0, min(12.0, round(gain_db, 1)))
        self._trigger_apo_sync()

    def set_bypass(self, bypass: bool):
        """Toggle bypass state."""
        self.bypass = bypass
        self._trigger_apo_sync()

    def reset_flat(self):
        """Reset all bands and enhancements to flat (0 dB)."""
        self.bands = [0.0] * 10
        self.bass_boost = 0
        self.vocal_clarity = 0
        self.treble_air = 0
        self.preamp = 0.0
        self._trigger_apo_sync()

    def apply_preset(self, preset_name: str) -> bool:
        """Apply a preset by name."""
        p = None
        if preset_name in DEFAULT_PRESETS:
            p = DEFAULT_PRESETS[preset_name]
        elif preset_name in self.custom_presets:
            p = self.custom_presets[preset_name]

        if p:
            self.bands = list(p["bands"])
            self.bass_boost = p.get("bass_boost", 0)
            self.vocal_clarity = p.get("vocal_clarity", 0)
            self.treble_air = p.get("treble_air", 0)
            self.preamp = p.get("preamp", -2.0)
            self._trigger_apo_sync()
            return True
        return False

    def save_custom_preset(self, name: str, description: str = ""):
        """Save current configuration as a new custom preset."""
        self.custom_presets[name] = {
            "description": description or "使用者自訂調音預設",
            "bands": list(self.bands),
            "bass_boost": self.bass_boost,
            "vocal_clarity": self.vocal_clarity,
            "treble_air": self.treble_air,
            "preamp": self.preamp
        }
        self.save_custom_presets_to_file()

    def delete_custom_preset(self, name: str) -> bool:
        """Delete a custom preset."""
        if name in self.custom_presets:
            del self.custom_presets[name]
            self.save_custom_presets_to_file()
            return True
        return False

    def load_custom_presets(self):
        """Load custom presets from disk."""
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r", encoding="utf-8") as f:
                    self.custom_presets = json.load(f)
            except Exception as e:
                print(f"Error loading custom presets: {e}")
                self.custom_presets = {}

    def save_custom_presets_to_file(self):
        """Save custom presets to disk."""
        try:
            with open(self.presets_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_presets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving custom presets: {e}")

    def get_effective_frequency_response(self, freqs: np.ndarray) -> np.ndarray:
        """
        Calculate total effective frequency response in dB across arbitrary frequencies,
        taking into account:
        1. 10 EQ bands with smooth cubic interpolation
        2. Bass Boost shelf (boosting < 100 Hz)
        3. Vocal Clarity bell (centered at 2.5 kHz)
        4. Treble Air shelf (boosting > 8 kHz)
        """
        if self.bypass:
            return np.zeros_like(freqs, dtype=np.float64)

        log_iso = np.log10(EQ_FREQUENCIES)
        log_f = np.log10(np.clip(freqs, 20.0, 22000.0))

        # Base 10-band response with monotonic cubic spline
        base_gains = np.interp(log_f, log_iso, self.bands)

        # Additional enhancements:
        # 1. Bass Boost (+0 to +6 dB at 40Hz tapering to 0 at 160Hz)
        bb_gain = (self.bass_boost / 100.0) * 6.5
        bass_curve = bb_gain / (1.0 + (freqs / 80.0) ** 2)

        # 2. Vocal Clarity (+0 to +5 dB peaking at 2.5 kHz with Q~1.5)
        vc_gain = (self.vocal_clarity / 100.0) * 5.0
        vocal_curve = vc_gain * np.exp(-0.5 * ((np.log2(freqs / 2500.0)) / 0.8) ** 2)

        # 3. Treble Air (+0 to +5 dB high shelf starting at 8 kHz)
        ta_gain = (self.treble_air / 100.0) * 5.0
        treble_curve = ta_gain * (1.0 / (1.0 + (10000.0 / np.maximum(1.0, freqs)) ** 3))

        total_curve = base_gains + bass_curve + vocal_curve + treble_curve
        return total_curve

    def force_sync(self):
        """Immediately write current EQ settings to Equalizer APO without debounce."""
        self._write_apo_config()

    def _trigger_apo_sync(self):
        """Debounced write to Equalizer APO config.txt."""
        if not self.sync_apo_enabled or not self.apo_installed:
            return

        with self._apo_lock:
            if self._write_timer is not None:
                self._write_timer.cancel()
            self._write_timer = threading.Timer(0.015, self._write_apo_config)
            self._write_timer.daemon = True
            self._write_timer.start()

    def _write_apo_config(self):
        """Write current EQ & Preamp parameters directly to Equalizer APO config.txt."""
        with self._apo_lock:
            try:
                # 31 ISO standard 1/3 octave frequencies for ultra-smooth APO GraphicEQ
                iso_31 = [
                    20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
                    200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600,
                    2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000
                ]

                if self.bypass:
                    preamp_str = "Preamp: 0.0 dB\n"
                    eq_pairs = [f"{f} 0.0" for f in iso_31]
                else:
                    gains_31 = self.get_effective_frequency_response(np.array(iso_31, dtype=np.float64))
                    preamp_str = f"Preamp: {self.preamp:.1f} dB\n"
                    eq_pairs = [f"{f} {g:.1f}" for f, g in zip(iso_31, gains_31)]

                graphic_eq_str = "GraphicEQ: " + "; ".join(eq_pairs) + "\n"

                content = (
                    "# ========================================================\n"
                    "# Generated by Desktop Audio Tuner & Equalizer Pro\n"
                    "# Real-time Windows Sound Quality Optimization\n"
                    "# ========================================================\n"
                    f"{preamp_str}"
                    f"{graphic_eq_str}"
                )

                with open(APO_CONFIG_FILE, "w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass

            except Exception as e:
                print(f"Error updating Equalizer APO: {e}")
