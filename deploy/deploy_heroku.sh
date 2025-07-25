#!/bin/bash
# Script de Deploy Rápido para Heroku
# Execute este script amanhã para fazer o deploy

echo "🚀 INICIANDO DEPLOY HEROKU - PLATAFORMA CS2"
echo "=========================================="

# 1. Verificar se Heroku CLI está instalado
echo "📋 Verificando Heroku CLI..."
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI não encontrado. Instale em: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# 2. Login no Heroku
echo "🔐 Fazendo login no Heroku..."
heroku login

# 3. Criar aplicação Heroku
echo "🆕 Criando aplicação Heroku..."
read -p "Digite o nome da aplicação (ex: minha-plataforma-cs2): " APP_NAME
heroku create $APP_NAME

# 4. Adicionar PostgreSQL
echo "🐘 Adicionando PostgreSQL..."
heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME

# 5. Configurar variáveis de ambiente básicas
echo "⚙️ Configurando variáveis de ambiente..."
heroku config:set FLASK_ENV=production --app $APP_NAME
heroku config:set FLASK_DEBUG=False --app $APP_NAME
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") --app $APP_NAME

# 6. Deploy
echo "🚀 Fazendo deploy..."
git add .
git commit -m "Deploy para produção - $(date)"
git push heroku main

# 7. Executar migrações
echo "📊 Executando migrações do banco..."
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()" --app $APP_NAME

# 8. Criar usuário admin
echo "👤 Criando usuário admin..."
heroku run python create_admin_docker.py --app $APP_NAME

echo "✅ DEPLOY CONCLUÍDO!"
echo "📱 Acesse: https://$APP_NAME.herokuapp.com"
echo "🔑 Admin: https://$APP_NAME.herokuapp.com/admin/login"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Configure as chaves Steam no Heroku dashboard"
echo "2. Configure domínio GoDaddy (se necessário)"
echo "3. Teste todas as funcionalidades"
