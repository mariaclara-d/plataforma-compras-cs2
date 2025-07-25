# Script de Deploy Rápido para Heroku - Windows PowerShell
# Execute este script amanhã para fazer o deploy

Write-Host "🚀 INICIANDO DEPLOY HEROKU - PLATAFORMA CS2" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 1. Verificar se Heroku CLI está instalado
Write-Host "📋 Verificando Heroku CLI..." -ForegroundColor Yellow
try {
    heroku --version | Out-Null
    Write-Host "✅ Heroku CLI encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Heroku CLI não encontrado. Instale em: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Red
    exit 1
}

# 2. Login no Heroku
Write-Host "🔐 Fazendo login no Heroku..." -ForegroundColor Yellow
heroku login

# 3. Criar aplicação Heroku
Write-Host "🆕 Criando aplicação Heroku..." -ForegroundColor Yellow
$APP_NAME = Read-Host "Digite o nome da aplicação (ex: minha-plataforma-cs2)"
heroku create $APP_NAME

# 4. Adicionar PostgreSQL
Write-Host "🐘 Adicionando PostgreSQL..." -ForegroundColor Yellow
heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME

# 5. Configurar variáveis de ambiente básicas
Write-Host "⚙️ Configurando variáveis de ambiente..." -ForegroundColor Yellow
$SECRET_KEY = -join ((1..64) | ForEach {[char]((97..122) + (48..57) | Get-Random)})
heroku config:set FLASK_ENV=production --app $APP_NAME
heroku config:set FLASK_DEBUG=False --app $APP_NAME
heroku config:set SECRET_KEY=$SECRET_KEY --app $APP_NAME

# 6. Deploy
Write-Host "🚀 Fazendo deploy..." -ForegroundColor Yellow
git add .
$COMMIT_MSG = "Deploy para produção - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git commit -m $COMMIT_MSG
git push heroku main

# 7. Executar migrações
Write-Host "📊 Executando migrações do banco..." -ForegroundColor Yellow
heroku run "python -c `"from app import app, db; app.app_context().push(); db.create_all()`"" --app $APP_NAME

# 8. Criar usuário admin
Write-Host "👤 Criando usuário admin..." -ForegroundColor Yellow
heroku run python create_admin_docker.py --app $APP_NAME

Write-Host "✅ DEPLOY CONCLUÍDO!" -ForegroundColor Green
Write-Host "📱 Acesse: https://$APP_NAME.herokuapp.com" -ForegroundColor Cyan
Write-Host "🔑 Admin: https://$APP_NAME.herokuapp.com/admin/login" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Configure as chaves Steam no Heroku dashboard"
Write-Host "2. Configure domínio GoDaddy (se necessário)"
Write-Host "3. Teste todas as funcionalidades"

# Abrir Heroku dashboard
$OPEN_DASHBOARD = Read-Host "Deseja abrir o dashboard do Heroku? (s/n)"
if ($OPEN_DASHBOARD -eq "s" -or $OPEN_DASHBOARD -eq "S") {
    Start-Process "https://dashboard.heroku.com/apps/$APP_NAME"
}
