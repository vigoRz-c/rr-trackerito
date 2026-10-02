Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\rrtrackerito.exe" & chr(34), 0
Set WshShell = Nothing
