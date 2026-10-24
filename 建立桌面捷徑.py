"""
Utility script to create a Windows Desktop Shortcut for Desktop Audio Tuner Pro.
Directly targets pythonw.exe for instant, windowless, reliable GUI startup.
"""

import os
import sys

def create_desktop_shortcut():
    try:
        import win32com.client
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
        import win32com.client

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop_dir = shell.SpecialFolders("Desktop")
    shortcut_path = os.path.join(desktop_dir, "Desktop Audio Tuner Pro.lnk")

    app_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(app_dir, "assets", "app_icon.ico")
    main_py = os.path.join(app_dir, "main.py")
    pythonw_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")

    shortcut = shell.CreateShortCut(shortcut_path)
    if os.path.exists(pythonw_exe):
        shortcut.TargetPath = pythonw_exe
        shortcut.Arguments = f'"{main_py}"'
    else:
        vbs_path = os.path.join(app_dir, "啟動音效等化器.vbs")
        shortcut.TargetPath = "wscript.exe"
        shortcut.Arguments = f'"{vbs_path}"'

    shortcut.WorkingDirectory = app_dir
    shortcut.IconLocation = f"{icon_path},0"
    shortcut.Description = "Desktop Audio Tuner & Equalizer Pro (電腦音質優化與等化器調音)"
    shortcut.WindowStyle = 1  # 1 = Normal Window
    shortcut.save()

    print(f"桌面捷徑建立成功: {shortcut_path}")

if __name__ == "__main__":
    create_desktop_shortcut()
