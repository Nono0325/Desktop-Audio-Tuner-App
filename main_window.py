"""
Main Application Window for Desktop Audio Tuner & Equalizer Pro.
Combines 10-Band Graphic EQ, Interactive Response Curve, Studio Enhancement Knobs,
System-wide Equalizer APO real-time synchronization, Live System Audio Loopback Spectrum,
and Audio Test Bench.
"""

import os
import sys
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QCheckBox, QFrame,
    QFileDialog, QInputDialog, QMessageBox, QSystemTrayIcon,
    QMenu, QAction, QSizePolicy
)
import numpy as np

from equalizer_engine import (
    EqualizerEngine, EQ_FREQUENCIES, EQ_BAND_LABELS,
    EQ_BAND_DESCRIPTIONS, DEFAULT_PRESETS
)
from audio_dsp_player import AudioDspPlayer
from system_audio_monitor import SystemAudioMonitor
from eq_widgets import EQCurveWidget, SpectrumWidget, RotaryDialWidget
from app_styles import DARK_THEME_QSS


class MainWindow(QMainWindow):
    """Desktop Audio Tuner & Equalizer Pro Main Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Desktop Audio Tuner & Equalizer Pro - 電腦音質優化與等化器調音")
        self.resize(920, 860)
        self.setMinimumSize(800, 780)

        # App Icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico")
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.setWindowIcon(self.app_icon)
        else:
            self.app_icon = QIcon()

        # Core Engines
        self.eq_engine = EqualizerEngine()
        self.dsp_player = AudioDspPlayer()
        self.system_monitor = SystemAudioMonitor()

        # UI State
        self.sliders: List[QSlider] = []
        self.slider_val_labels: List[QLabel] = []
        self._updating_ui = False
        self.current_monitor_device = "預設音訊輸出"

        # Build UI & Connect Signals
        self.setStyleSheet(DARK_THEME_QSS)
        self._init_ui()
        self._setup_tray_icon()
        self._sync_all_to_ui()

        # Connect Live System Audio Loopback Monitor
        self.system_monitor.spectrum_ready.connect(self._on_system_spectrum_ready)
        self.system_monitor.device_info_ready.connect(self._on_device_info_ready)
        self.system_monitor.status_changed.connect(self._on_monitor_status_changed)
        self.system_monitor.start()

        # Connect Built-in Player Signals
        self.dsp_player.spectrum_updated.connect(self._on_player_spectrum_ready)
        self.dsp_player.playback_state_changed.connect(self._on_playback_state_changed)
        self.dsp_player.position_updated.connect(self._on_position_updated)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 16, 18, 14)
        main_layout.setSpacing(10)

        # ==========================================
        # 1. Top Header: Logo, APO Status, Bypass, Pin
        # ==========================================
        header_card = QFrame()
        header_card.setObjectName("cardFrame")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        # Brand / Logo
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)
        title_label = QLabel("Desktop Audio Tuner Pro")
        title_label.setObjectName("appTitleLabel")
        subtitle_label = QLabel("Windows 全系統音質優化與即時 10-Band EQ")
        subtitle_label.setObjectName("appSubTitleLabel")
        brand_layout.addWidget(title_label)
        brand_layout.addWidget(subtitle_label)
        header_layout.addLayout(brand_layout)

        # Equalizer APO Status Badge
        if self.eq_engine.apo_installed:
            self.apo_badge = QLabel("● Windows 全系統已連線 (APO)")
            self.apo_badge.setObjectName("apoBadgeActive")
            self.apo_badge.setToolTip("所有由 Windows 輸出的音訊 (Spotify, YouTube, 遊戲, 影音) 皆受此調音優化！")
        else:
            self.apo_badge = QLabel("● 內建即時 DSP 引擎模式")
            self.apo_badge.setObjectName("apoBadgeInactive")
            self.apo_badge.setToolTip("未偵測到 Equalizer APO，目前正在即時測試台模式運行。")
        header_layout.addWidget(self.apo_badge)

        header_layout.addStretch()

        # Prominent A/B Bypass / Audition Button
        self.btn_bypass = QPushButton("🟢 【等化器優化已生效】(點擊切換原音比對)")
        self.btn_bypass.setObjectName("bypassBtnNormal")
        self.btn_bypass.setMinimumWidth(260)
        self.btn_bypass.setToolTip("在「原音直通 (Bypass)」與「等化器優化」之間無縫切換，瞬間感受自己播放音樂的音質對比！")
        self.btn_bypass.setCheckable(True)
        self.btn_bypass.clicked.connect(self._toggle_bypass)
        header_layout.addWidget(self.btn_bypass)

        # Stay on Top
        self.chk_stay_on_top = QCheckBox("視窗置頂")
        self.chk_stay_on_top.setToolTip("保持調音器在所有遊戲與視窗最上層")
        self.chk_stay_on_top.stateChanged.connect(self._toggle_stay_on_top)
        header_layout.addWidget(self.chk_stay_on_top)

        # Tray Button
        btn_tray = QPushButton("最小化至系統匣")
        btn_tray.setToolTip("縮小至右下角工作列系統匣，背景持續為全電腦優化音質")
        btn_tray.clicked.connect(self.hide)
        header_layout.addWidget(btn_tray)

        main_layout.addWidget(header_card)

        # ==========================================
        # 2. Preset Selection & Output Device Bar
        # ==========================================
        preset_card = QFrame()
        preset_card.setObjectName("cardFrame")
        preset_layout = QHBoxLayout(preset_card)
        preset_layout.setContentsMargins(14, 8, 14, 8)
        preset_layout.setSpacing(10)

        lbl_preset = QLabel("調音情境預設:")
        lbl_preset.setObjectName("sectionTitle")
        preset_layout.addWidget(lbl_preset)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(250)
        self._refresh_presets_combo()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)

        # Save Preset Button
        btn_save_preset = QPushButton("💾 儲存自訂預設")
        btn_save_preset.setToolTip("將目前的 EQ 與音質旋鈕設定儲存為新預設")
        btn_save_preset.clicked.connect(self._save_custom_preset_dialog)
        preset_layout.addWidget(btn_save_preset)

        # Delete Preset Button
        self.btn_del_preset = QPushButton("🗑️ 刪除")
        self.btn_del_preset.setToolTip("刪除選中的使用者自訂預設")
        self.btn_del_preset.clicked.connect(self._delete_custom_preset_action)
        preset_layout.addWidget(self.btn_del_preset)

        preset_layout.addStretch()

        # Output Device Selector (for loopback monitor)
        lbl_dev = QLabel("監聽輸出裝置:")
        lbl_dev.setObjectName("sectionTitle")
        preset_layout.addWidget(lbl_dev)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(180)
        self._populate_output_devices()
        self.device_combo.currentIndexChanged.connect(self._on_monitor_device_changed)
        preset_layout.addWidget(self.device_combo)

        # Reset Flat Button
        btn_reset_flat = QPushButton("⟲ 全部重設平直 (Flat)")
        btn_reset_flat.setToolTip("將所有頻段推桿與強化旋鈕重設為 0 dB 平直原音")
        btn_reset_flat.clicked.connect(self._reset_flat_action)
        preset_layout.addWidget(btn_reset_flat)

        main_layout.addWidget(preset_card)

        # ==========================================
        # 3. Frequency Response Curve & Real-Time Spectrum
        # ==========================================
        vis_card = QFrame()
        vis_card.setObjectName("cardFrame")
        vis_layout = QVBoxLayout(vis_card)
        vis_layout.setContentsMargins(12, 10, 12, 10)
        vis_layout.setSpacing(6)

        self.curve_widget = EQCurveWidget()
        self.curve_widget.band_changed.connect(self._on_curve_point_dragged)
        vis_layout.addWidget(self.curve_widget, 1)

        # Real-time Spectrum Analyzer
        self.spectrum_widget = SpectrumWidget()
        vis_layout.addWidget(self.spectrum_widget)

        main_layout.addWidget(vis_card, 1)

        # ==========================================
        # 4. 10-Band Vertical EQ Sliders Section
        # ==========================================
        sliders_card = QFrame()
        sliders_card.setObjectName("cardFrame")
        sliders_layout = QHBoxLayout(sliders_card)
        sliders_layout.setContentsMargins(14, 12, 14, 12)
        sliders_layout.setSpacing(8)

        for i, (freq_label, desc) in enumerate(zip(EQ_BAND_LABELS, EQ_BAND_DESCRIPTIONS)):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignCenter)

            # Gain Label (+0.0 dB)
            lbl_gain = QLabel("0.0 dB")
            lbl_gain.setAlignment(Qt.AlignCenter)
            lbl_gain.setStyleSheet("font-weight: 700; color: #58a6ff; font-size: 11px;")
            self.slider_val_labels.append(lbl_gain)
            col.addWidget(lbl_gain)

            # Vertical Slider (-120 to +120 -> -12.0 to +12.0 dB)
            slider = QSlider(Qt.Vertical)
            slider.setRange(-120, 120)
            slider.setValue(0)
            slider.setMinimumHeight(125)
            slider.setToolTip(f"{freq_label} ({desc})\n點兩下重設為 0.0 dB")
            slider.valueChanged.connect(lambda val, idx=i: self._on_slider_changed(idx, val))
            self.sliders.append(slider)
            col.addWidget(slider)

            # Frequency Label (e.g. 1 kHz)
            lbl_freq = QLabel(freq_label)
            lbl_freq.setAlignment(Qt.AlignCenter)
            lbl_freq.setStyleSheet("font-weight: 700; color: #e6edf3; font-size: 11px;")
            col.addWidget(lbl_freq)

            # Sub description
            lbl_sub = QLabel(desc.split(" ")[0])
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet("color: #8b9bb4; font-size: 9px;")
            col.addWidget(lbl_sub)

            sliders_layout.addLayout(col)

        main_layout.addWidget(sliders_card)

        # ==========================================
        # 5. Studio Sound Enhancement Knobs (Dials)
        # ==========================================
        knobs_card = QFrame()
        knobs_card.setObjectName("cardFrame")
        knobs_layout = QHBoxLayout(knobs_card)
        knobs_layout.setContentsMargins(14, 10, 14, 10)
        knobs_layout.setSpacing(14)

        # Bass Boost Knob
        self.dial_bass = RotaryDialWidget("重低音加強", 0, 100, 0, "%")
        self.dial_bass.setToolTip("提升 40-80 Hz 低頻飽滿度與打擊感 (點兩下重設)")
        self.dial_bass.value_changed.connect(self._on_bass_boost_changed)
        knobs_layout.addWidget(self.dial_bass)

        # Vocal Clarity Knob
        self.dial_vocal = RotaryDialWidget("人聲清晰度", 0, 100, 0, "%")
        self.dial_vocal.setToolTip("強化 1.5k-3.5kHz 人聲對白與咬字清晰度 (點兩下重設)")
        self.dial_vocal.value_changed.connect(self._on_vocal_clarity_changed)
        knobs_layout.addWidget(self.dial_vocal)

        # Treble Air Knob
        self.dial_treble = RotaryDialWidget("高頻通透度", 0, 100, 0, "%")
        self.dial_treble.setToolTip("增強 10k-16kHz 細膩空氣感與樂器光澤 (點兩下重設)")
        self.dial_treble.value_changed.connect(self._on_treble_air_changed)
        knobs_layout.addWidget(self.dial_treble)

        # Preamp Gain Knob (-20 to +12 dB)
        self.dial_preamp = RotaryDialWidget("前級增益", -20.0, 12.0, -2.0, "dB")
        self.dial_preamp.setToolTip("總前級增益衰減/放大，防止等化器增益後數位爆音 (點兩下重設)")
        self.dial_preamp.value_changed.connect(self._on_preamp_changed)
        knobs_layout.addWidget(self.dial_preamp)

        main_layout.addWidget(knobs_card)

        # ==========================================
        # 6. Audio Test Bench & Real-Time Player
        # ==========================================
        player_card = QFrame()
        player_card.setObjectName("cardFrame")
        player_layout = QHBoxLayout(player_card)
        player_layout.setContentsMargins(14, 8, 14, 8)
        player_layout.setSpacing(10)

        # Play/Pause Button
        self.btn_play = QPushButton("播放試聽 ▶")
        self.btn_play.setObjectName("primaryBtn")
        self.btn_play.setFixedWidth(95)
        self.btn_play.clicked.connect(self._toggle_playback)
        player_layout.addWidget(self.btn_play)

        # Stop Button
        btn_stop = QPushButton("停止 ■")
        btn_stop.setFixedWidth(65)
        btn_stop.clicked.connect(self.dsp_player.stop)
        player_layout.addWidget(btn_stop)

        # Track Selector
        self.track_combo = QComboBox()
        self.track_combo.addItem("頻率掃描 (20Hz - 20kHz 快速音場檢測)")
        self.track_combo.addItem("重低音衝擊 (Sub-Bass Drop 測試)")
        self.track_combo.addItem("人聲與樂器和弦 (Acoustic Harmony 試聽)")
        self.track_combo.addItem("粉紅噪音 (Pink Noise 聲學校正)")
        self.track_combo.addItem("📂 載入本機音樂檔案 (WAV/MP3/FLAC)...")
        self.track_combo.currentIndexChanged.connect(self._on_track_selected)
        player_layout.addWidget(self.track_combo, 1)

        # Seek Slider
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(lambda v: self.dsp_player.seek_normalized(v / 1000.0))
        player_layout.addWidget(self.seek_slider, 1)

        # Time label
        self.lbl_time = QLabel("0:00 / 0:00")
        self.lbl_time.setStyleSheet("color: #8b9bb4; font-size: 11px;")
        player_layout.addWidget(self.lbl_time)

        # Volume Slider
        lbl_vol = QLabel("試聽音量:")
        lbl_vol.setStyleSheet("color: #8b9bb4;")
        player_layout.addWidget(lbl_vol)

        slider_vol = QSlider(Qt.Horizontal)
        slider_vol.setRange(0, 100)
        slider_vol.setValue(50)
        slider_vol.setFixedWidth(75)
        slider_vol.valueChanged.connect(lambda v: self.dsp_player.set_volume(v / 100.0))
        player_layout.addWidget(slider_vol)

        main_layout.addWidget(player_card)

        # Status Bar
        self.statusBar().showMessage("準備就緒 | 等化器已同步至 Windows 系統音效，支援 YouTube / Spotify 即時響應")

    def _setup_tray_icon(self):
        """Setup Windows system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.setToolTip("Desktop Audio Tuner Pro - 電腦音效調音優化中")

        tray_menu = QMenu()
        show_action = QAction("開啟調音面板", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)

        bypass_action = QAction("切換 A/B 直通比較", self)
        bypass_action.triggered.connect(self._toggle_bypass)
        tray_menu.addAction(bypass_action)

        tray_menu.addSeparator()
        quit_action = QAction("退出調音器", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def _populate_output_devices(self):
        self.device_combo.clear()
        self.device_combo.addItem("預設系統輸出 (自動追蹤)")
        devs = self.system_monitor.get_output_devices()
        for d in devs:
            short = d.split("(")[0].strip() if "(" in d else d
            self.device_combo.addItem(short, d)

    def _on_monitor_device_changed(self, index: int):
        if index == 0:
            self.system_monitor.set_device(None)
        else:
            dev_name = self.device_combo.currentData()
            self.system_monitor.set_device(dev_name)

    def _on_system_spectrum_ready(self, bars: np.ndarray):
        """Receive live spectrum from whatever music Windows is currently playing."""
        if not self.dsp_player.is_playing:
            self.spectrum_widget.set_spectrum(bars)

    def _on_player_spectrum_ready(self, bars: np.ndarray):
        """Receive spectrum from built-in audio player."""
        if self.dsp_player.is_playing:
            self.spectrum_widget.set_spectrum(bars)

    def _on_device_info_ready(self, device_name: str):
        self.current_monitor_device = device_name
        self.spectrum_widget.set_monitor_status(device_name, self.system_monitor._running)

    def _on_monitor_status_changed(self, is_active: bool):
        self.spectrum_widget.set_monitor_status(self.current_monitor_device, is_active)
        if is_active and not self.dsp_player.is_playing:
            self.statusBar().showMessage(f"● 正在即時響應系統播放音樂: {self.current_monitor_device}")

    def _toggle_stay_on_top(self, state):
        on = (state == Qt.Checked)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on)
        self.show()

    def _toggle_bypass(self):
        new_state = not self.eq_engine.bypass
        self.eq_engine.set_bypass(new_state)
        self.eq_engine.force_sync()
        if new_state:
            self.btn_bypass.setText("🟠 【原音直通 (Bypass)】(點擊開啟等化器優化)")
            self.btn_bypass.setObjectName("bypassBtnActive")
            self.statusBar().showMessage("已開啟原音直通 (Bypass) - 正在聆聽未修飾的原始聲音 (可用於對比調音效果)")
        else:
            self.btn_bypass.setText("🟢 【等化器優化已生效】(點擊切換原音比對)")
            self.btn_bypass.setObjectName("bypassBtnNormal")
            self.statusBar().showMessage("已套用等化器音質優化！全系統聲音立即更新。")
        self.btn_bypass.setStyle(self.btn_bypass.style())
        self._sync_dsp_player_and_curve()

    def _refresh_presets_combo(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for p in DEFAULT_PRESETS.keys():
            self.preset_combo.addItem(p)
        if self.eq_engine.custom_presets:
            self.preset_combo.insertSeparator(self.preset_combo.count())
            for cp in self.eq_engine.custom_presets.keys():
                self.preset_combo.addItem(f"★ {cp}")
        self.preset_combo.blockSignals(False)

    def _on_preset_selected(self, index: int):
        text = self.preset_combo.currentText()
        if not text:
            return
        name = text.replace("★ ", "")
        if self.eq_engine.apply_preset(name):
            self.eq_engine.force_sync()
            self._sync_all_to_ui()
            self.statusBar().showMessage(f"已套用調音預設: {name} (全系統聲音立即同步)")

    def _save_custom_preset_dialog(self):
        name, ok = QInputDialog.getText(self, "儲存自訂預設", "請輸入新預設名稱:")
        if ok and name.strip():
            preset_name = name.strip()
            self.eq_engine.save_custom_preset(preset_name)
            self._refresh_presets_combo()
            self.preset_combo.setCurrentText(f"★ {preset_name}")
            self.statusBar().showMessage(f"自訂預設「{preset_name}」已儲存！")

    def _delete_custom_preset_action(self):
        text = self.preset_combo.currentText()
        if text.startswith("★ "):
            name = text.replace("★ ", "")
            reply = QMessageBox.question(
                self, "確認刪除", f"確定要刪除自訂預設「{name}」嗎？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.eq_engine.delete_custom_preset(name)
                self._refresh_presets_combo()
                self.preset_combo.setCurrentIndex(0)
                self.statusBar().showMessage(f"自訂預設「{name}」已刪除。")
        else:
            QMessageBox.information(self, "提示", "內建出廠預設無法刪除。")

    def _reset_flat_action(self):
        self.eq_engine.reset_flat()
        self.eq_engine.force_sync()
        self._sync_all_to_ui()
        self.statusBar().showMessage("已將所有等化器推桿與旋鈕重設為 0.0 dB 平直原音。")

    def _on_slider_changed(self, band_idx: int, val: int):
        if self._updating_ui:
            return
        gain_db = val / 10.0
        self.slider_val_labels[band_idx].setText(f"{gain_db:+.1f} dB")
        self.eq_engine.set_band(band_idx, gain_db)
        self._sync_dsp_player_and_curve()

    def _on_curve_point_dragged(self, band_idx: int, gain_db: float):
        self._updating_ui = True
        self.sliders[band_idx].setValue(int(gain_db * 10))
        self.slider_val_labels[band_idx].setText(f"{gain_db:+.1f} dB")
        self.eq_engine.set_band(band_idx, gain_db)
        self._updating_ui = False
        self._sync_dsp_player_and_curve()

    def _on_bass_boost_changed(self, val: float):
        self.eq_engine.set_bass_boost(int(val))
        self._sync_dsp_player_and_curve()

    def _on_vocal_clarity_changed(self, val: float):
        self.eq_engine.set_vocal_clarity(int(val))
        self._sync_dsp_player_and_curve()

    def _on_treble_air_changed(self, val: float):
        self.eq_engine.set_treble_air(int(val))
        self._sync_dsp_player_and_curve()

    def _on_preamp_changed(self, val: float):
        self.eq_engine.set_preamp(val)
        self._sync_dsp_player_and_curve()

    def _sync_all_to_ui(self):
        """Update all slider positions, labels, and dials from engine state."""
        self._updating_ui = True
        for i in range(10):
            gain = self.eq_engine.bands[i]
            self.sliders[i].setValue(int(gain * 10))
            self.slider_val_labels[i].setText(f"{gain:+.1f} dB")

        self.dial_bass.set_value(self.eq_engine.bass_boost)
        self.dial_vocal.set_value(self.eq_engine.vocal_clarity)
        self.dial_treble.set_value(self.eq_engine.treble_air)
        self.dial_preamp.set_value(self.eq_engine.preamp)

        self._updating_ui = False
        self._sync_dsp_player_and_curve()

    def _sync_dsp_player_and_curve(self):
        """Update live curve view and real-time DSP preview filter."""
        self.curve_widget.set_parameters(
            self.eq_engine.bands,
            self.eq_engine.bass_boost,
            self.eq_engine.vocal_clarity,
            self.eq_engine.treble_air,
            self.eq_engine.preamp,
            self.eq_engine.bypass
        )
        self.dsp_player.update_dsp_filters(
            self.eq_engine.bands,
            self.eq_engine.bass_boost,
            self.eq_engine.vocal_clarity,
            self.eq_engine.treble_air,
            self.eq_engine.preamp,
            self.eq_engine.bypass
        )

    # ==========================
    # Audio Player Handlers
    # ==========================
    def _toggle_playback(self):
        if self.dsp_player.is_playing:
            self.dsp_player.pause()
        else:
            self.dsp_player.play()

    def _on_playback_state_changed(self, is_playing: bool):
        if is_playing:
            self.btn_play.setText("暫停 ❚❚")
        else:
            self.btn_play.setText("播放試聽 ▶")

    def _on_position_updated(self, cur_sec: float, total_sec: float):
        if total_sec > 0:
            if not self.seek_slider.isSliderDown():
                self.seek_slider.setValue(int(cur_sec / total_sec * 1000.0))
            cur_min = int(cur_sec // 60)
            cur_s = int(cur_sec % 60)
            tot_min = int(total_sec // 60)
            tot_s = int(total_sec % 60)
            self.lbl_time.setText(f"{cur_min}:{cur_s:02d} / {tot_min}:{tot_s:02d}")

    def _on_track_selected(self, index: int):
        text = self.track_combo.currentText()
        if "載入本機音樂檔案" in text:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "選擇音樂檔案進行調音試聽", "",
                "音訊檔案 (*.wav *.mp3 *.flac *.ogg *.m4a);;所有檔案 (*.*)"
            )
            if file_path:
                if self.dsp_player.load_audio_file(file_path):
                    self.track_combo.setItemText(index, f"🎵 {os.path.basename(file_path)}")
                    self.statusBar().showMessage(f"已載入音樂: {os.path.basename(file_path)}")
                    self.dsp_player.play()
                else:
                    QMessageBox.warning(self, "載入失敗", "無法讀取此音訊檔案。")
            else:
                self.track_combo.setCurrentIndex(0)
        else:
            self.dsp_player.load_preset_track(text)
            self.statusBar().showMessage(f"已載入測試音效: {text}")

    def _quit_application(self):
        self.dsp_player.stop()
        self.system_monitor.stop()
        self.tray_icon.hide()
        sys.exit(0)

    def closeEvent(self, event):
        """Minimize to tray on window close, instead of exiting."""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Desktop Audio Tuner Pro",
                "調音器已縮小至系統匣，持續為全系統提供音質優化！",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            self.dsp_player.stop()
            self.system_monitor.stop()
            event.accept()
