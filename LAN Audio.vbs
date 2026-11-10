Option Explicit
Dim shell, files, folder, python, entry, candidate
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
python = ""
For Each entry In Split(shell.ExpandEnvironmentStrings("%PATH%"), ";")
    entry = Replace(Trim(entry), Chr(34), "")
    If Len(entry) > 0 Then
        candidate = files.BuildPath(entry, "pythonw.exe")
        If files.FileExists(candidate) Then
            python = candidate
            Exit For
        End If
    End If
Next
If Len(python) = 0 Then
    MsgBox "Khong tim thay Python. Hay cai Python 3 voi Tcl/Tk va them vao PATH, roi chay start.cmd.", 48, "LAN Audio"
Else
    shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & folder & "\app\gui.py" & Chr(34), 1, False
End If
