@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Ambiente virtual nao encontrado na pasta .venv
  echo Crie com:  python -m venv .venv  ^&^&  .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -c "import re,pathlib,sys; p=pathlib.Path('chaves/.env'); t=p.read_text(encoding='utf-8') if p.exists() else ''; m=re.search(r'^BOT_TOKEN=(.+)$', t, re.M); sys.exit(0 if (m and m.group(1).strip()) else 1)"
if errorlevel 1 (
  echo.
  echo [ATENCAO] O BOT_TOKEN ainda nao foi preenchido.
  echo 1. Abra o arquivo:  chaves\.env
  echo 2. Cole o token do @BotFather em:  BOT_TOKEN=...
  echo 3. Salve e rode este arquivo novamente.
  echo.
  notepad "chaves\.env"
  pause
  exit /b 1
)

echo.
echo ============================================
echo   LinguaBot iniciando... (feche para parar)
echo ============================================
echo.
".venv\Scripts\python.exe" -m linguabot
echo.
echo O bot foi encerrado.
pause
