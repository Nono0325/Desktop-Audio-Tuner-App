# Desktop Audio Tuner & Equalizer Pro (電腦音質優化與等化器調音器)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6)
![Equalizer APO](https://img.shields.io/badge/Equalizer%20APO-Integrated-brightgreen)
![GUI](https://img.shields.io/badge/GUI-PyQt5%20Native-purple)
![License](https://img.shields.io/badge/License-MIT-green)

專為 Windows 電腦設計的高階音質優化與 10-Band 等化器（EQ）調音桌面應用程式（**非網頁、純原生桌面程式**）。深度整合 Windows 核心音訊處理架構（Equalizer APO），能直接對整台電腦的所有聲音輸出（包括 Spotify、YouTube、遊戲、Discord、Netflix、電影與系統音效）進行零延遲的即時調音與音質強化。

---

## 🌟 核心特色

### 1. 🎛️ Windows 全系統音效即時優化
- **即時零延遲調音**：自動整合 Windows Equalizer APO，任何拉動推桿或切換預設的操作，電腦當下播放的任何聲音均會立即同步改變。
- **全域 A/B 快速比對**：一鍵在「原音直通 (Bypass)」與「等化器優化」之間無縫切換，瞬間感受音質提升的對比差異。
- **軟體防爆音 (Soft Limiter & Preamp)**：提供可調節前級增益（-20 dB 至 +12 dB），避免等化器過度增益時產生的數位失真（Clipping）。

### 2. 📊 互動式頻率響應曲線與頻譜分析儀
- **10 頻段 ISO 標準等化器**：
  - `31 Hz`：超重低音 (Sub-bass)
  - `63 Hz`：重低音打擊感 (Punch)
  - `125 Hz`：低頻厚度與溫暖感 (Warmth)
  - `250 Hz`：低中頻飽滿度 (Low Mid)
  - `500 Hz`：中頻主體 (Body)
  - `1 kHz`：人聲與樂器清晰度 (Clarity)
  - `2 kHz`：穿透力與咬字 (Presence)
  - `4 kHz`：臨場感與細節 (Detail)
  - `8 kHz`：高頻光澤感 (Brilliance)
  - `16 kHz`：極高頻通透空氣感 (Air)
- **平滑樣條曲線 (Cubic Spline)**：即時繪製真實頻率響應曲線，並支援滑鼠直接拖曳控制點進行調節。
- **動態 48 頻段動態頻譜儀 (Spectrum Analyzer)**：具備峰值保持 (Peak Hold) 與重力衰減的專業頻譜視覺化。

### 3. 🎚️ 4 大工作室級音效旋鈕 (Studio Dials)
- 🔊 **重低音加強 (Bass Boost)**：增強 40~80 Hz 低頻動態飽滿度，適合低音愛好者。
- 🎙️ **人聲清晰度 (Vocal Clarity)**：凸顯 1.5k~3.5kHz 人聲對白與說話咬字，視訊會議、看影片必備。
- ✨ **高頻通透度 (Treble Air)**：增加 10k~16kHz 極高頻透明感與細節。
- 🎚️ **前級增益 (Preamp)**：控制進入等化器前的訊號電平，點兩下快速歸零。

### 4. 🎵 10 款精心調校情境預設
| 預設名稱 | 適用情境與聲學特性 |
| :--- | :--- |
| **🎵 流行音樂 (Pop)** | 飽滿有力的低頻節奏，人聲靠前清晰，高頻通透 |
| **🎸 搖滾金屬 (Rock & Metal)** | 強勁大鼓打擊感，電吉他穿透力強，高鈸清脆不刺耳 |
| **🔊 極致重低音 (Bass Boost & EDM)** | 深沉震動的極低頻，電音派對、Hip-Hop 震撼低音轟炸 |
| **🎙️ 人聲清晰 / Podcast (Vocal Clarity)**| 濾除低頻悶響，凸顯人聲演講對白，視訊會議首選 |
| **🎬 電影劇院震撼 (Cinema 3D)** | 寬廣立體動態空間感，電影爆炸場景震撼，對白清晰分明 |
| **🎮 FPS 聽聲辨位 (Gaming Footsteps)** | 壓抑轟炸低頻，強化 1.5k-4kHz 腳步聲、換彈聲與方位感 |
| **🎻 古典自然交響 (Classical)** | 純淨自然的管弦樂平衡，器樂層次分明，細膩優雅 |
| **🌙 深夜防爆音模式 (Night Mode)** | 收斂過強低頻與刺耳高音，夜間看片追劇不吵醒家人 |
| **🎧 耳機通透音場 (Headphone Soundstage)**| 補償封閉式耳機頭中效應，擴大立體聲音場，久聽不累 |
| **⚖️ 平直原音直通 (Flat Reference)** | 原始無修飾平直響應，專業監聽真實聲音 |

*亦支援儲存、命名、刪除個人的自訂預設！*

### 5. 🎧 即時試聽測試台 (Audio Test Bench)
- 內建聲學校正訊號：
  - `20 Hz - 20 kHz 頻率掃描`（快速檢驗耳機/喇叭各頻率響應與共振）
  - `重低音衝擊測試`（Sub-Bass Drop 測試低音下潛能力）
  - `粉紅噪音 (Pink Noise)`（專業聲學校正標準訊號）
  - `人聲與樂器和弦`（豐富諧波音軌）
- 支援**載入本機音樂檔案**（WAV、MP3、FLAC、OGG 等），直接邊播邊調音。

### 6. 💻 系統匣常駐與置頂功能
- **系統匣背景執行**：點擊右上角關閉或「最小化至系統匣」，程式將安靜於右下角常駐，持續優化全電腦聲音，不佔用工作列空間。
- **視窗置頂**：方便在打遊戲、看影片、聽歌時浮動操作調音。

---

## 🚀 快速啟動方式

### 方法 1：雙擊桌面捷徑（最推薦）
執行專案目錄下的 `建立桌面捷徑.py`：
```powershell
python 建立桌面捷徑.py
```
之後即可直接從 Windows 桌面的 **Desktop Audio Tuner Pro** 捷徑一鍵無黑框啟動！

### 方法 2：雙擊啟動腳本
- `啟動音效等化器.vbs`：**靜默無黑框啟動**（推薦日常使用）
- `啟動音效等化器.bat`：終端機啟動（帶有環境檢查）

---

## 🛠️ 環境需求與手動安裝

1. **作業系統**：Windows 10 / Windows 11 (64-bit)
2. **Python**：3.10 以上
3. **安裝依賴套件**：
```powershell
pip install -r requirements.txt
```
4. **全系統調音整合**：
本程式自動偵測並相容已安裝的 **[Equalizer APO](https://sourceforge.net/projects/equalizerapo/)**。當 Equalizer APO 存在時，所有調音將自動即時套用至整個 Windows 系統音訊輸出！

---

## 📂 專案檔案架構

```
c:\Nono\tuner\
├── assets\
│   ├── app_icon.ico       # 應用程式 256x256 高畫質圖示
│   └── app_icon.png       # 高解析度 Logo 圖
├── equalizer_engine.py    # 10 頻段 EQ 演算、音效強化與 Equalizer APO 即時同步引擎
├── audio_dsp_player.py    # 即時試聽音訊播放器、串聯 Biquad IIR 濾波器與訊號產生器
├── eq_widgets.py          # 自定義繪製互動響應曲線、動態頻譜儀、工作室旋鈕
├── app_styles.py          # 高階深色工作台 QSS 樣式系統
├── main_window.py         # 主視窗整合介面、推桿陣列與系統匣常駐
├── main.py                # 應用程式進入點 (含 High-DPI 與 Windows 任務欄圖示支援)
├── 啟動音效等化器.vbs      # 靜默無黑框啟動腳本
├── 啟動音效等化器.bat      # Windows 批次檔啟動器
├── 建立桌面捷徑.py        # 一鍵建立桌面捷徑工具
├── requirements.txt       # Python 套件依賴清單
└── README.md              # 說明手冊
```

---

## 📄 License
MIT License.
