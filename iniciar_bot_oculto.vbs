' Inicia o LinguaBot em segundo plano (sem janela).
' Usado pela inicializacao automatica do Windows.
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = projectDir
python = projectDir & "\.venv\Scripts\pythonw.exe"

If fso.FileExists(python) Then
    ' pythonw.exe roda sem console
    shell.Run """" & python & """ -m linguabot", 0, False
Else
    python2 = projectDir & "\.venv\Scripts\python.exe"
    If fso.FileExists(python2) Then
        shell.Run """" & python2 & """ -m linguabot", 0, False
    End If
End If
