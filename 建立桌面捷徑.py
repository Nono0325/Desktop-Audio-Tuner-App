"""
Utility script to create a Windows Desktop Shortcut for Desktop Audio Tuner Pro.
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
    vbs_path = os.path.join(app_dir, "啟動音效等化器.vbs")
    icon_path = os.path.join(app_dir, "assets", "app_icon.ico")

    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = f'"{vbs_path}"'
    shortcut.WorkingDirectory = app_dir
    shortcut.IconLocation = f"{icon_path},0"
    shortcut.Description = "Desktop Audio Tuner & Equalizer Pro"
    shortcut.save()

    print(f"桌面捷徑建立成功: {shortcut_path}")

if __name__ == "__main__":
    create_desktop_shortcut()
