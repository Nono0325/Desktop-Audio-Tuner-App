"""
Real-time Audio DSP Player & Sound Bench.
Provides high-fidelity preview playback with real-time 10-band biquad filtering,
instant A/B bypass comparison, synthetic acoustic test signals, and FFT spectrum analysis.
"""

import math
import os
import threading
import time
from typing import Dict, List, Optional
import numpy as np
import scipy.signal
import sounddevice as sd
from PyQt5.QtCore import QObject, pyqtSignal


def make_biquad_peaking(f0: float, gain_db: float, q: float = 1.414, fs: float = 44100.0) -> np.ndarray:
    """Generate RBJ Peaking EQ biquad SOS section [b0, b1, b2, 1, a1, a2]."""
    if abs(gain_db) < 0.05:
        return np.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)

    f0 = max(20.0, min(fs * 0.45, f0))
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2.0 * q)

    b0 = 1.0 + alpha * A
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / A

    return np.array([b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0], dtype=np.float64)


def make_biquad_lowshelf(f0: float, gain_db: float, fs: float = 44100.0) -> np.ndarray:
    """Generate RBJ Low Shelf biquad SOS section."""
    if abs(gain_db) < 0.05:
        return np.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)

    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / fs
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / 2.0 * math.sqrt(2.0)

    b0 = A * ((A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * math.sqrt(A) * alpha)
    b1 = 2.0 * A * ((A - 1.0) - (A + 1.0) * cos_w0)
    b2 = A * ((A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * math.sqrt(A) * alpha)
    a0 = (A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * math.sqrt(A) * alpha
    a1 = -2.0 * ((A - 1.0) + (A + 1.0) * cos_w0)
    a2 = (A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * math.sqrt(A) * alpha

    return np.array([b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0], dtype=np.float64)


def make_biquad_highshelf(f0: float, gain_db: float, fs: float = 44100.0) -> np.ndarray:
    """Generate RBJ High Shelf biquad SOS section."""
    if abs(gain_db) < 0.05:
        return np.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)

    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / fs
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / 2.0 * math.sqrt(2.0)

    b0 = A * ((A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * math.sqrt(A) * alpha)
    b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0)
    b2 = A * ((A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * math.sqrt(A) * alpha)
    a0 = (A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * math.sqrt(A) * alpha
    a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0)
    a2 = (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * math.sqrt(A) * alpha

    return np.array([b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0], dtype=np.float64)


class AudioDspPlayer(QObject):
    """
    Background audio player that streams sound through a real-time
    parametric EQ biquad cascade and emits spectrum data for visualization.
    """

    spectrum_updated = pyqtSignal(np.ndarray)  # Emits 48-band magnitude spectrum
    playback_state_changed = pyqtSignal(bool)   # is_playing
    playback_finished = pyqtSignal()
    position_updated = pyqtSignal(float, float) # (current_sec, total_sec)

    def __init__(self, sample_rate: int = 44100):
        super().__init__()
        self.sample_rate = sample_rate
        self.is_playing = False
        self.is_bypass = False
        self.volume = 0.5  # 0.0 to 1.0
        self.current_pos = 0

        # Current audio buffer (stereo float32)
        self.audio_buffer: Optional[np.ndarray] = None
        self.track_name = "頻率掃描 (20Hz - 20kHz 快速音場檢測)"

        # DSP Filter state
        self._sos_cascade: Optional[np.ndarray] = None
        self._preamp_gain = 1.0
        self._lock = threading.Lock()
        self.stream: Optional[sd.OutputStream] = None

        # Filter memories for seamless block processing
        self._zi_left: Optional[np.ndarray] = None
        self._zi_right: Optional[np.ndarray] = None

        # Load initial synthetic track
        self.load_preset_track(self.track_name)

    def update_dsp_filters(self, bands: List[float], bass_boost: int, vocal_clarity: int, treble_air: int, preamp_db: float, bypass: bool):
        """Recompute cascaded biquad coefficients."""
        with self._lock:
            self.is_bypass = bypass
            self._preamp_gain = 10.0 ** (preamp_db / 20.0)

            if bypass:
                self._sos_cascade = None
                return

            fs = float(self.sample_rate)
            sections = []

            # 1. 10 Peaking Bands
            freqs = [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
            for f, g in zip(freqs, bands):
                if abs(g) > 0.05:
                    sections.append(make_biquad_peaking(f, g, q=1.414, fs=fs))

            # 2. Bass Boost (Low Shelf at 80 Hz)
            if bass_boost > 0:
                bb_db = (bass_boost / 100.0) * 6.0
                sections.append(make_biquad_lowshelf(80.0, bb_db, fs=fs))

            # 3. Vocal Clarity (Peaking at 2.5 kHz)
            if vocal_clarity > 0:
                vc_db = (vocal_clarity / 100.0) * 5.0
                sections.append(make_biquad_peaking(2500.0, vc_db, q=1.2, fs=fs))

            # 4. Treble Air (High Shelf at 9 kHz)
            if treble_air > 0:
                ta_db = (treble_air / 100.0) * 5.0
                sections.append(make_biquad_highshelf(9000.0, ta_db, fs=fs))

            if sections:
                self._sos_cascade = np.vstack(sections)
                # Reinitialize filter state if filter structure changed
                n_sections = len(sections)
                if self._zi_left is None or self._zi_left.shape[0] != n_sections:
                    self._zi_left = np.zeros((n_sections, 2), dtype=np.float64)
                    self._zi_right = np.zeros((n_sections, 2), dtype=np.float64)
            else:
                self._sos_cascade = None

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))

    def load_preset_track(self, track_name: str):
        """Synthesize high-quality acoustic test signals."""
        self.stop()
        self.track_name = track_name
        sr = self.sample_rate

        if "頻率掃描" in track_name:
            # 8-second log frequency sweep from 20 Hz to 20,000 Hz
            dur = 8.0
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            f0, f1 = 20.0, 20000.0
            phase = 2.0 * np.pi * f0 * ((f1 / f0) ** (t / dur) - 1.0) / np.log(f1 / f0)
            sig = 0.35 * np.sin(phase)
            env = np.ones_like(sig)
            env[:int(sr * 0.1)] = np.linspace(0, 1, int(sr * 0.1))
            env[-int(sr * 0.1):] = np.linspace(1, 0, int(sr * 0.1))
            sig *= env
            self.audio_buffer = np.column_stack([sig, sig]).astype(np.float32)

        elif "重低音" in track_name:
            # 8-second rhythmic bass test: 45Hz sub-bass drone with 60Hz punch drops
            dur = 8.0
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            sig = np.zeros_like(t)
            # 2 beats per second
            bpm = 120
            beat_len = sr * 60 // bpm
            n_beats = len(t) // beat_len
            for b in range(n_beats):
                start = b * beat_len
                end = min(len(t), start + beat_len)
                bt = (np.arange(end - start)) / sr
                # Pitch drop 120Hz -> 45Hz
                f_inst = 45.0 + 75.0 * np.exp(-18.0 * bt)
                phase = 2.0 * np.pi * np.cumsum(f_inst) / sr
                kick = 0.5 * np.sin(phase) * np.exp(-4.5 * bt)
                sub = 0.25 * np.sin(2.0 * np.pi * 38.0 * bt) * np.exp(-2.0 * bt)
                sig[start:end] += (kick + sub)
            self.audio_buffer = np.column_stack([sig, sig]).astype(np.float32)

        elif "粉紅噪音" in track_name:
            # 10-second pink noise (1/f power spectrum) for acoustic tuning
            dur = 10.0
            n_samples = int(sr * dur)
            white = np.random.randn(n_samples)
            # Simple Voss-McCartney or IIR pinking filter
            b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
            a = [1.0, -2.494956002, 2.017265875, -0.522189400]
            pink = scipy.signal.lfilter(b, a, white)
            pink = (pink / (np.max(np.abs(pink)) + 1e-6) * 0.28).astype(np.float32)
            self.audio_buffer = np.column_stack([pink, pink]).astype(np.float32)

        else:
            # 10-second rich harmonic musical chords (C - G - Am - F)
            dur = 10.0
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            sig = np.zeros_like(t)
            chords = [
                ([130.81, 164.81, 196.0, 261.63, 392.0], 2.5),  # C
                ([98.0, 146.83, 196.0, 246.94, 392.0], 2.5),   # G
                ([110.0, 164.81, 220.0, 261.63, 440.0], 2.5),  # Am
                ([87.31, 130.81, 174.61, 261.63, 349.23], 2.5), # F
            ]
            cur_idx = 0
            for chord_freqs, chord_dur in chords:
                c_samples = int(chord_dur * sr)
                ct = np.linspace(0, chord_dur, c_samples, endpoint=False)
                c_sig = np.zeros(c_samples)
                for f in chord_freqs:
                    c_sig += 0.12 * np.sin(2 * np.pi * f * ct)
                    c_sig += 0.05 * np.sin(2 * np.pi * (2 * f) * ct)
                    c_sig += 0.02 * np.sin(2 * np.pi * (3 * f) * ct)
                c_sig *= np.exp(-1.2 * ct)
                end_idx = min(len(sig), cur_idx + c_samples)
                sig[cur_idx:end_idx] += c_sig[:end_idx - cur_idx]
                cur_idx = end_idx

            sig = (sig / (np.max(np.abs(sig)) + 1e-6) * 0.4).astype(np.float32)
            self.audio_buffer = np.column_stack([sig, sig]).astype(np.float32)

        self.current_pos = 0

    def load_audio_file(self, file_path: str) -> bool:
        """Load external audio file (WAV, MP3, FLAC, etc.)."""
        self.stop()
        try:
            import soundfile as sf
            data, sr = sf.read(file_path, dtype='float32')
            if sr != self.sample_rate:
                # Resample to match player sample rate
                num_samples = int(len(data) * self.sample_rate / sr)
                data = scipy.signal.resample(data, num_samples)

            if data.ndim == 1:
                self.audio_buffer = np.column_stack([data, data]).astype(np.float32)
            else:
                self.audio_buffer = data[:, :2].astype(np.float32)

            self.track_name = os.path.basename(file_path)
            self.current_pos = 0
            return True
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False

    def play(self):
        if self.is_playing:
            return
        if self.audio_buffer is None or len(self.audio_buffer) == 0:
            return

        self.is_playing = True
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                dtype='float32',
                blocksize=1024,
                callback=self._audio_callback
            )
            self.stream.start()
            self.playback_state_changed.emit(True)
        except Exception as e:
            print(f"Error starting playback: {e}")
            self.is_playing = False
            self.playback_state_changed.emit(False)

    def pause(self):
        self.is_playing = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        self.playback_state_changed.emit(False)

    def stop(self):
        self.pause()
        self.current_pos = 0
        if self.audio_buffer is not None:
            total_sec = len(self.audio_buffer) / self.sample_rate
            self.position_updated.emit(0.0, total_sec)

    def seek_normalized(self, ratio: float):
        """Seek to position (0.0 to 1.0)."""
        if self.audio_buffer is not None:
            self.current_pos = int(np.clip(ratio, 0.0, 1.0) * len(self.audio_buffer))

    def _audio_callback(self, outdata, frames, time_info, status):
        if not self.is_playing or self.audio_buffer is None:
            outdata.fill(0)
            return

        buf_len = len(self.audio_buffer)
        if self.current_pos >= buf_len:
            # Loop playback
            self.current_pos = 0

        end_pos = self.current_pos + frames
        if end_pos <= buf_len:
            chunk = self.audio_buffer[self.current_pos:end_pos].copy()
            self.current_pos = end_pos
        else:
            first_len = buf_len - self.current_pos
            rem_len = frames - first_len
            chunk = np.vstack([self.audio_buffer[self.current_pos:], self.audio_buffer[:rem_len]]).copy()
            self.current_pos = rem_len

        # Apply DSP in real-time
        with self._lock:
            sos = self._sos_cascade
            preamp = self._preamp_gain
            vol = self.volume
            bypass = self.is_bypass

        if not bypass and sos is not None:
            try:
                # Filter left and right channels
                left, self._zi_left = scipy.signal.sosfilt(sos, chunk[:, 0], zi=self._zi_left)
                right, self._zi_right = scipy.signal.sosfilt(sos, chunk[:, 1], zi=self._zi_right)
                chunk[:, 0] = left * preamp
                chunk[:, 1] = right * preamp
            except Exception:
                pass

        # Soft-clipping limiter to prevent digital distortion
        chunk *= vol
        chunk = np.tanh(chunk * 0.95)
        outdata[:] = chunk

        # Emit progress
        cur_sec = self.current_pos / self.sample_rate
        total_sec = buf_len / self.sample_rate
        self.position_updated.emit(cur_sec, total_sec)

        # Compute FFT spectrum for visualizer
        mono = 0.5 * (chunk[:, 0] + chunk[:, 1])
        if len(mono) >= 512:
            fft_vals = np.abs(np.fft.rfft(mono[:512]))
            freqs = np.fft.rfftfreq(512, 1.0 / self.sample_rate)
            log_edges = np.logspace(np.log10(30), np.log10(18000), 49)
            bars = np.zeros(48, dtype=np.float32)
            for i in range(48):
                m = (freqs >= log_edges[i]) & (freqs < log_edges[i+1])
                if np.any(m):
                    bars[i] = np.mean(fft_vals[m])
            max_b = np.max(bars)
            if max_b > 1e-4:
                bars = np.clip(bars / (max_b * 0.9 + 0.1), 0.0, 1.0)
            self.spectrum_updated.emit(bars)
