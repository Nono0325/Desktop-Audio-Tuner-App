Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Automatically detect Pythonw path
pythonwPath = "C:\Users\hungr\anaconda3\pythonw.exe"
If Not fso.FileExists(pythonwPath) Then
    pythonwPath = "pythonw.exe"
End If

' Use window style 1 (Normal) so the GUI window is displayed, without console window
WshShell.Run """" & pythonwPath & """ """ & currentDir & "\main.py""", 1, False
