"""
Real-time System Audio Loopback Monitor.
Captures whatever audio Windows is currently playing (YouTube, Spotify, Games, Media Player)
via WASAPI Loopback, calculates live 48-band FFT spectrum & RMS volume,
and provides instant visual feedback in the GUI.
"""

import math
import sys
import threading
import time
from typing import Dict, List, Optional
import numpy as np
import soundcard as sc
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class SystemAudioMonitor(QThread):
    """
    Background worker that continuously captures Windows desktop output audio
    and emits live spectrum data and volume levels to the UI.
    """

    spectrum_ready = pyqtSignal(np.ndarray)  # 48-band normalized spectrum array
    level_ready = pyqtSignal(float)          # Current RMS audio level [0.0, 1.0]
    device_info_ready = pyqtSignal(str)      # Display name of monitored output device
    status_changed = pyqtSignal(bool)        # True if audio is actively playing

    def __init__(self, sample_rate: int = 44100, block_size: int = 1024):
        super().__init__()
        self.sample_rate = sample_rate
        self.block_size = block_size
        self._running = False
        self._lock = threading.Lock()

        self.selected_device_name: Optional[str] = None
        self.smooth_bars = np.zeros(48, dtype=np.float32)

        # Precompute log-spaced frequency bin edges from 25 Hz to 18,000 Hz
        self.n_bins = 48
        self.bin_edges = np.logspace(np.log10(25.0), np.log10(18000.0), self.n_bins + 1)
        self.fft_freqs = np.fft.rfftfreq(self.block_size, 1.0 / self.sample_rate)
        self.window = np.hanning(self.block_size)

        # Precompute frequency masks for fast FFT binning
        self.bin_masks = []
        for i in range(self.n_bins):
            mask = (self.fft_freqs >= self.bin_edges[i]) & (self.fft_freqs < self.bin_edges[i + 1])
            self.bin_masks.append(mask)

    def get_output_devices(self) -> List[str]:
        """List all available Windows output playback devices."""
        try:
            speakers = sc.all_speakers()
            return [s.name for s in speakers]
        except Exception:
            return []

    def set_device(self, device_name: Optional[str]):
        """Switch monitored output device."""
        with self._lock:
            self.selected_device_name = device_name

    def stop(self):
        """Request the loopback recording loop to stop."""
        self._running = False
        self.wait(1000)

    def run(self):
        self._running = True

        while self._running:
            try:
                # Find target speaker device
                with self._lock:
                    target_name = self.selected_device_name

                if target_name:
                    try:
                        speaker = sc.get_speaker(target_name)
                    except Exception:
                        speaker = sc.default_speaker()
                else:
                    speaker = sc.default_speaker()

                display_name = speaker.name
                self.device_info_ready.emit(display_name)

                # Get loopback microphone for this speaker
                loopback_mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)

                with loopback_mic.recorder(
                    samplerate=self.sample_rate,
                    channels=2,
                    blocksize=self.block_size
                ) as recorder:
                    silence_count = 0

                    while self._running:
                        # Check if device was switched
                        with self._lock:
                            if self.selected_device_name != target_name and self.selected_device_name is not None:
                                break

                        # Record next chunk of desktop audio
                        data = recorder.record(numframes=self.block_size)
                        if data is None or len(data) == 0:
                            time.sleep(0.01)
                            continue

                        # Convert stereo to mono
                        mono = 0.5 * (data[:, 0] + data[:, 1])
                        rms = float(np.sqrt(np.mean(mono ** 2)))

                        # Check if actively playing
                        if rms > 0.0005:
                            silence_count = 0
                            self.status_changed.emit(True)
                        else:
                            silence_count += 1
                            if silence_count > 15:
                                self.status_changed.emit(False)

                        self.level_ready.emit(rms)

                        # FFT Spectral Analysis
                        windowed = mono * self.window
                        fft_magnitudes = np.abs(np.fft.rfft(windowed))

                        raw_bars = np.zeros(self.n_bins, dtype=np.float32)
                        for i in range(self.n_bins):
                            mask = self.bin_masks[i]
                            if np.any(mask):
                                raw_bars[i] = float(np.mean(fft_magnitudes[mask]))

                        # Dynamic range compression & normalization
                        if rms > 0.0005:
                            # Logarithmic visual scaling
                            norm_bars = np.log10(1.0 + raw_bars * 12.0)
                            max_val = np.max(norm_bars)
                            if max_val > 0.05:
                                norm_bars = np.clip(norm_bars / (max_val * 0.75 + 0.15), 0.0, 1.0)
                            else:
                                norm_bars.fill(0.0)

                            # Smooth temporal response
                            self.smooth_bars = 0.65 * norm_bars + 0.35 * self.smooth_bars
                        else:
                            self.smooth_bars *= 0.85

                        self.spectrum_ready.emit(self.smooth_bars)

            except Exception as e:
                # Device disconnected or sleeping, wait briefly and retry
                time.sleep(0.5)

        self._running = False
