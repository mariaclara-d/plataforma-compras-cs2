#!/usr/bin/env pwsh
# 🚀 Deploy Automatizado para Heroku - CS2 Marketplace
# Versão: 1.0 | Data: Oct 2025

Write-Host "🚀 INICIANDO DEPLOY HEROKU - CS2 MARKETPLACE" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# 1. Verificações pré-deploy
Write-Host "`n📋 VERIFICAÇÕES PRÉ-DEPLOY..." -ForegroundColor Yellow

# Verificar se Heroku CLI está instalado
try {
    $herokuVersion = heroku --version
    Write-Host "✅ Heroku CLI: $herokuVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Heroku CLI não encontrado! Instale: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Red
    exit 1
}

# Verificar se está logado no Heroku
try {
    $herokuUser = heroku auth:whoami
    Write-Host "✅ Logado como: $herokuUser" -ForegroundColor Green
} catch {
    Write-Host "❌ Não logado no Heroku! Execute: heroku login" -ForegroundColor Red
    exit 1
}

# Verificar arquivos essenciais
$requiredFiles = @("Procfile", "requirements.txt", "app.py", "db_config.py")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file encontrado" -ForegroundColor Green
    } else {
        Write-Host "❌ $file não encontrado!" -ForegroundColor Red
        exit 1
    }
}

# 2. Configurar aplicação Heroku
Write-Host "`n🏗️  CONFIGURANDO APLICAÇÃO..." -ForegroundColor Yellow

$appName = Read-Host "Digite o nome da aplicação Heroku (ou Enter para auto-gerar)"
if ([string]::IsNullOrWhiteSpace($appName)) {
    $appName = "cs2-marketplace-$(Get-Random -Minimum 1000 -Maximum 9999)"
}

try {
    Write-Host "Criando aplicação: $appName" -ForegroundColor Cyan
    heroku create $appName --region us
    Write-Host "✅ Aplicação criada: https://$appName.herokuapp.com" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Aplicação já existe ou erro na criação. Continuando..." -ForegroundColor Yellow
}

# 3. Configurar PostgreSQL
Write-Host "`n🐘 CONFIGURANDO POSTGRESQL..." -ForegroundColor Yellow
try {
    heroku addons:create heroku-postgresql:mini -a $appName
    Write-Host "✅ PostgreSQL configurado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  PostgreSQL já configurado ou erro. Continuando..." -ForegroundColor Yellow
}

# 4. Configurar variáveis de ambiente essenciais
Write-Host "`n🔧 CONFIGURANDO VARIÁVEIS DE AMBIENTE..." -ForegroundColor Yellow

# Gerar SECRET_KEY segura
$secretKey = -join ((1..50) | ForEach {[char]((65..90) + (97..122) + (48..57) | Get-Random)})

$envVars = @{
    "FLASK_ENV" = "production"
    "SECRET_KEY" = $secretKey
    "WTF_CSRF_ENABLED" = "True"
    "SITE_URL" = "https://$appName.herokuapp.com"
}

foreach ($key in $envVars.Keys) {
    $value = $envVars[$key]
    try {
        heroku config:set "$key=$value" -a $appName
        Write-Host "✅ $key configurado" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Erro ao configurar $key" -ForegroundColor Yellow
    }
}

# 5. Deploy do código
Write-Host "`n📦 FAZENDO DEPLOY DO CÓDIGO..." -ForegroundColor Yellow

try {
    # Commit atual (se houver mudanças)
    git add .
    git commit -m "🚀 Deploy to Heroku - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ErrorAction SilentlyContinue
    
    # Push para Heroku
    git push heroku main
    Write-Host "✅ Código enviado para Heroku" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro no deploy do código!" -ForegroundColor Red
    exit 1
}

# 6. Executar migrações de banco
Write-Host "`n🗄️  EXECUTANDO MIGRAÇÕES..." -ForegroundColor Yellow
try {
    heroku run python -c "from app import create_app; from db_config import db; app = create_app(); app.app_context().push(); db.create_all()" -a $appName
    Write-Host "✅ Banco de dados inicializado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Erro nas migrações. Execute manualmente se necessário." -ForegroundColor Yellow
}

# 7. Verificar logs e status
Write-Host "`n📊 VERIFICANDO STATUS..." -ForegroundColor Yellow
try {
    heroku ps -a $appName
    Write-Host "✅ Aplicação rodando" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Verificar logs para problemas" -ForegroundColor Yellow
}

# 8. Resultado final
Write-Host "`n🎉 DEPLOY CONCLUÍDO!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "🌐 URL da Aplicação: https://$appName.herokuapp.com" -ForegroundColor Cyan
Write-Host "📱 Dashboard Heroku: https://dashboard.heroku.com/apps/$appName" -ForegroundColor Cyan
Write-Host "`n📋 PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Configure as variáveis Steam API no dashboard Heroku" -ForegroundColor White
Write-Host "2. Teste as funcionalidades principais" -ForegroundColor White
Write-Host "3. Configure domínio customizado (opcional)" -ForegroundColor White
Write-Host "`n🔧 COMANDOS ÚTEIS:" -ForegroundColor Yellow
Write-Host "heroku logs --tail -a $appName  # Ver logs em tempo real" -ForegroundColor White
Write-Host "heroku config -a $appName       # Ver variáveis de ambiente" -ForegroundColor White
Write-Host "heroku restart -a $appName      # Reiniciar aplicação" -ForegroundColor White

Write-Host "`n✅ Deploy finalizado com sucesso!" -ForegroundColor Green
