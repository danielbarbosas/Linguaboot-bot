@echo off
setlocal
echo Encerrando o LinguaBot...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*linguabot*' -and $_.Name -like 'python*' } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force; Write-Host ('Parado PID ' + $_.ProcessId) } catch {} }"
echo Concluido.
timeout /t 2 >nul
