"""
Modern Studio Dark Theme QSS Stylesheet for Desktop Audio Tuner & Equalizer Pro.
High-end metallic obsidian finish with neon cyan (#00e5ff), emerald green (#00e676), and violet accents.
Optimized for high-DPI scaling and responsive spacing to prevent text clipping.
"""

DARK_THEME_QSS = """
/* Global Window & Font */
QWidget {
    background-color: #0b0f17;
    color: #e6edf3;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Microsoft JhengHei", sans-serif;
    font-size: 12px;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}

/* Card Containers */
QFrame#cardFrame {
    background-color: #131924;
    border: 1px solid #243042;
    border-radius: 10px;
}

QFrame#subCardFrame {
    background-color: #0e131d;
    border: 1px solid #1c2636;
    border-radius: 8px;
}

/* Header Banner */
QLabel#appTitleLabel {
    font-size: 17px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.5px;
}

QLabel#appSubTitleLabel {
    font-size: 11px;
    font-weight: 600;
    color: #00e5ff;
}

QLabel#apoBadgeActive {
    background-color: #11281e;
    color: #00e676;
    border: 1px solid #00e676;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#apoBadgeInactive {
    background-color: #2b1d1d;
    color: #ff7b72;
    border: 1px solid #ff7b72;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
}

/* Section Titles */
QLabel#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #8b9bb4;
    letter-spacing: 0.5px;
}

/* Buttons */
QPushButton {
    background-color: #1c2536;
    color: #c9d5e8;
    border: 1px solid #2b394e;
    border-radius: 6px;
    padding: 5px 10px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #26334a;
    color: #ffffff;
    border-color: #48658a;
}

QPushButton:pressed {
    background-color: #151d2b;
}

QPushButton:checked {
    background-color: #1f6feb;
    color: #ffffff;
    border-color: #58a6ff;
}

/* Primary Action Buttons */
QPushButton#primaryBtn {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
    font-weight: 700;
    padding: 5px 12px;
}

QPushButton#primaryBtn:hover {
    background-color: #2ea043;
}

QPushButton#bypassBtnActive {
    background-color: #3d2314;
    color: #ff9b50;
    border: 1px solid #ff9b50;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 6px;
}

QPushButton#bypassBtnNormal {
    background-color: #142e24;
    color: #00e676;
    border: 1px solid #00e676;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 6px;
}

/* ComboBox */
QComboBox {
    background-color: #131924;
    color: #e6edf3;
    border: 1px solid #2b394e;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 20px;
    font-weight: 600;
    font-size: 12px;
}

QComboBox:hover {
    border-color: #00e5ff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #2b394e;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8b9bb4;
    margin-right: 4px;
}

QComboBox QAbstractItemView {
    background-color: #131924;
    color: #e6edf3;
    border: 1px solid #2b394e;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* Vertical EQ Sliders */
QSlider::groove:vertical {
    width: 6px;
    background: #1c2636;
    border-radius: 3px;
}

QSlider::add-page:vertical {
    background: #00e5ff;
    border-radius: 3px;
}

QSlider::sub-page:vertical {
    background: #1c2636;
    border-radius: 3px;
}

QSlider::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.4 #d1d5db, stop:1.0 #9ca3af);
    border: 1px solid #2b394e;
    height: 18px;
    width: 20px;
    margin-left: -7px;
    margin-right: -7px;
    border-radius: 4px;
}

QSlider::handle:vertical:hover {
    background: #00e5ff;
    border-color: #ffffff;
}

/* Horizontal Player Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #1c2636;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #00e5ff;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #58a6ff;
    border: 2px solid #ffffff;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #79c0ff;
    width: 16px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 8px;
}

/* CheckBox */
QCheckBox {
    spacing: 6px;
    color: #c9d5e8;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #2b394e;
    background-color: #131924;
}

QCheckBox::indicator:hover {
    border-color: #00e5ff;
}

QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #58a6ff;
}

/* Tooltips */
QToolTip {
    background-color: #131924;
    color: #e6edf3;
    border: 1px solid #2b394e;
    padding: 5px 8px;
    border-radius: 6px;
}

/* Status Bar */
QStatusBar {
    background-color: #080b10;
    color: #8b9bb4;
    font-size: 11px;
    border-top: 1px solid #1c2636;
    padding: 2px 8px;
}
"""
