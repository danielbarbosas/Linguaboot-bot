# Grava o token do @BotFather em chaves\.env sem editar o arquivo na mao.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root 'chaves\.env'

if (-not (Test-Path $envFile)) {
    Write-Host "[ERRO] Arquivo nao encontrado: $envFile" -ForegroundColor Red
    exit 1
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " LinguaBot - configurar token do Telegram" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "No Telegram: abra o @BotFather, envie /newbot e copie o TOKEN."
Write-Host ""

$token = (Read-Host "Cole o token aqui").Trim()

if ($token -notmatch '^\d{6,}:[A-Za-z0-9_-]{30,}$') {
    Write-Host "[ERRO] Formato invalido. O token se parece com 123456789:ABCdef..." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Validando o token no Telegram..."
try {
    $check = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getMe" -TimeoutSec 30
} catch {
    $check = $null
}

if (-not $check -or -not $check.ok) {
    Write-Host "[ERRO] O Telegram recusou este token (nao autorizado)." -ForegroundColor Red
    Write-Host "Possiveis causas: token digitado errado, revogado ou ja substituido." -ForegroundColor Yellow
    Write-Host "Abra o @BotFather, envie /mybots, escolha o bot e use 'API Token'." -ForegroundColor Yellow
    Write-Host "Se necessario, envie /revoke para gerar um token novo e tente de novo." -ForegroundColor Yellow
    exit 1
}

Write-Host ("[OK] Token valido. Bot: @" + $check.result.username + " (" + $check.result.first_name + ")") -ForegroundColor Green

$content = Get-Content $envFile -Raw
$content = [regex]::Replace($content, '(?m)^BOT_TOKEN=.*$', "BOT_TOKEN=$token")
Set-Content -Path $envFile -Value $content -Encoding UTF8

Write-Host ""
Write-Host "[OK] Token salvo em: $envFile" -ForegroundColor Green
Write-Host "Agora execute: iniciar_bot.bat" -ForegroundColor Green
