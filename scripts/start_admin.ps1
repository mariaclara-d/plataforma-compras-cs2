#!/usr/bin/env pwsh
# Script PowerShell para iniciar o sistema admin

Write-Host "=== SISTEMA ADMIN FLASK ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Parando containers existentes..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "2. Reconstruindo imagem..." -ForegroundColor Yellow
docker-compose build --no-cache web

Write-Host ""
Write-Host "3. Iniciando containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "4. Aguardando servicos iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "5. Verificando status..." -ForegroundColor Yellow
docker ps

Write-Host ""
Write-Host "=== SISTEMA PRONTO ===" -ForegroundColor Green
Write-Host ""
Write-Host "Acesse: http://localhost:5000/admin/login" -ForegroundColor White
Write-Host "Usuario: admin" -ForegroundColor White
Write-Host "Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Para verificar logs: docker-compose logs web" -ForegroundColor Gray
Write-Host "Para parar: docker-compose down" -ForegroundColor Gray
Write-Host ""
Read-Host "Pressione Enter para continuar"
