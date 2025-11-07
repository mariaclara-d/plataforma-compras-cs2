#  **DOCKER COMMANDS - Guia Completo**

##  **Comandos Essenciais do Projeto**

###  **Inicialização do Sistema**

```bash
# Iniciar todos os containers em modo detached
docker-compose up -d

# Iniciar e ver logs em tempo real
docker-compose up

# Iniciar apenas o serviço web
docker-compose up web

# Iniciar apenas o banco de dados
docker-compose up db
```

###  **Monitoramento e Status**

```bash
# Verificar status dos containers
docker-compose ps

# Ver logs de todos os serviços
docker-compose logs

# Ver logs em tempo real
docker-compose logs -f

# Ver logs apenas do web
docker-compose logs -f web

# Ver logs apenas do banco
docker-compose logs -f db

# Ver últimas 50 linhas dos logs
docker-compose logs --tail=50

# Ver logs com timestamps
docker-compose logs -t
```

###  **Gerenciamento de Containers**

```bash
# Parar todos os containers
docker-compose down

# Parar containers e remover volumes
docker-compose down -v

# Parar containers e remover imagens
docker-compose down --rmi all

# Reiniciar serviço específico
docker-compose restart web
docker-compose restart db

# Restart rápido apenas do web (mantém DB rodando)
docker-compose restart web && docker-compose logs -f web

# Parar serviço específico
docker-compose stop web

# Iniciar serviço específico parado
docker-compose start web
```

###  **Build e Rebuild**

```bash
# Build das imagens
docker-compose build

# Build forçado (sem cache)
docker-compose build --no-cache

# Build apenas do serviço web
docker-compose build web

# Build e iniciar
docker-compose up --build

# Rebuild completo (limpar e reconstruir)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

###  **Gerenciamento de Dados**

```bash
# Backup do banco PostgreSQL
docker-compose exec db pg_dump -U postgres csgo_skins > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose exec -T db psql -U postgres csgo_skins < backup_20250725_123000.sql

# Acessar shell do container do banco
docker-compose exec db psql -U postgres -d csgo_skins

# Acessar shell do container web
docker-compose exec web bash

# Executar comando Python no container
docker-compose exec web python scripts/create_admin.py
```

###  **Volumes e Limpeza**

```bash
# Listar volumes
docker volume ls

# Remover volumes não utilizados
docker volume prune

# Remover volume específico (CUIDADO!)
docker volume rm documentacaoflask---copia_postgres_data

# Ver informações do volume
docker volume inspect documentacaoflask---copia_postgres_data
```

###  **Debug e Troubleshooting**

```bash
# Verificar uso de recursos
docker stats

# Inspecionar container
docker-compose exec web ps aux

# Ver variáveis de ambiente
docker-compose exec web env

# Verificar conectividade entre containers
docker-compose exec web ping db

# Ver configuração do docker-compose
docker-compose config

# Validar docker-compose.yml
docker-compose config --quiet
```

###  **Limpeza do Sistema**

```bash
# Remover containers parados
docker container prune

# Remover imagens não utilizadas
docker image prune

# Remover redes não utilizadas
docker network prune

# Limpeza completa do Docker
docker system prune -a

# Limpeza com volumes (CUIDADO!)
docker system prune -a --volumes
```

###  **Comandos Administrativos**

```bash
# Criar administrador
docker-compose exec web python scripts/create_admin_docker.py

# Reset do banco de dados
docker-compose exec web python scripts/reset_db.py

# Executar migrações
docker-compose exec web flask db upgrade

# Backup automático
docker-compose exec web python scripts/backup_postgresql.py

# Popular dados de teste
docker-compose exec web python scripts/popular_teste.py
```

###  **Comandos de Rede**

```bash
# Listar redes Docker
docker network ls

# Inspecionar rede do projeto
docker network inspect documentacaoflask---copia_default

# Ver IPs dos containers
docker-compose exec web hostname -I
docker-compose exec db hostname -I
```

###  **Monitoramento Avançado**

```bash
# CPU e memória em tempo real
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Logs com filtro de erro
docker-compose logs | grep ERROR

# Logs com filtro de tempo
docker-compose logs --since="2025-07-25T10:00:00"

# Exportar logs para arquivo
docker-compose logs > app_logs_$(date +%Y%m%d_%H%M%S).log
```

##  **Scripts Utilitários**

###  **Script de Deploy Rápido** (`deploy/quick_deploy.sh`)

```bash
#!/bin/bash
echo " Deploy Rápido - TitoSkins v2.0"
docker-compose down
docker-compose pull
docker-compose build --no-cache
docker-compose up -d
echo " Deploy concluído!"
docker-compose ps
```

###  **Script de Restart Seguro** (`deploy/safe_restart.sh`)

```bash
#!/bin/bash
echo " Restart Seguro - TitoSkins v2.0"
docker-compose exec db pg_dump -U postgres csgo_skins > backup_before_restart_$(date +%Y%m%d_%H%M%S).sql
docker-compose restart web
docker-compose logs --tail=20 web
echo " Restart concluído!"
```

###  **Script de Recuperação Steam** (`deploy/steam_recovery.sh`)

```bash
#!/bin/bash
echo " Recuperação de Autenticação Steam"
echo " Verificando status do sistema..."

# Verificar logs de autenticação Steam
docker-compose logs web | grep -E "(LOGIN|STEAM|access_token|KeyError)" | tail -20

echo " Testando conectividade Steam..."
docker-compose exec web curl -s "https://steamcommunity.com" > /dev/null && echo " Steam acessível" || echo " Steam inacessível"

echo " Reiniciando com modo debug..."
docker-compose restart web
docker-compose logs -f web | grep -E "(LOGIN|STEAM|ERRO|ERROR)"
```

###  **Script de Diagnóstico Completo** (`deploy/full_diagnostic.sh`)

```bash
#!/bin/bash
echo " Diagnóstico Completo - TitoSkins v2.0"

echo "=== CONTAINERS ==="
docker-compose ps

echo "=== CONECTIVIDADE ==="
docker-compose exec web ping -c 3 db
docker-compose exec web curl -s http://localhost:5000/api/steam/status

echo "=== LOGS STEAM ==="
docker-compose logs web | grep -E "(STEAM|LOGIN|access_token)" | tail -10

echo "=== RECURSOS ==="
docker stats --no-stream

echo "=== VOLUMES ==="
docker volume ls | grep documentacao

echo " Diagnóstico concluído"
```

###  **Comandos de Diagnóstico**

```bash
# Status completo do sistema
docker-compose ps && docker stats --no-stream

# Saúde dos containers
docker-compose exec web curl -f http://localhost:5000/status || echo "Web não responde"
docker-compose exec db pg_isready -U postgres || echo "DB não responde"

# Espaço em disco
docker system df

# Verificar portas
docker-compose port web 5000
docker-compose port db 5432
```

##  **Comandos de Emergência**

###  **Reset Completo do Sistema**

```bash
#  CUIDADO: Remove TODOS os dados!
docker-compose down -v
docker system prune -a --volumes
docker-compose up --build -d
```

###  **Restart Forçado**

```bash
# Para containers travados
docker-compose kill
docker-compose rm -f
docker-compose up -d
```

###  **Recuperação de Desastre**

```bash
# 1. Parar tudo
docker-compose down

# 2. Backup de emergência (se possível)
docker run --rm -v documentacaoflask---copia_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# 3. Restaurar do backup mais recente
# (comandos específicos dependem do backup disponível)

# 4. Reiniciar sistema
docker-compose up --build -d
```

###  **Troubleshooting Steam Authentication (v2.0)**

```bash
# Verificar erros de autenticação Steam
docker-compose logs web | grep -E "(access_token|KeyError|STEAM.*ERRO)"

# Testar modo fallback de emergência
docker-compose exec web python -c "
import asyncio
from services.aiosteampy_service import enviar_oferta_aiosteampy
print(' Testando sistema de fallback...')
"

# Forçar restart com limpeza de sessão
docker-compose down
docker-compose up --build -d
docker-compose logs -f web | grep -E "(LOGIN|STEAM|ERRO)"

# Verificar conectividade Steam
docker-compose exec web curl -s "https://steamcommunity.com" && echo " Steam OK" || echo " Steam inacessível"
```

###  **Modo Fallback Manual**

```bash
# Ativar modo de simulação para testes
docker-compose exec web python -c "
print(' Ativando modo de simulação emergencial...')
print(' Use AssetIDs de teste: 31337001, 31337002, etc.')
print(' Ofertas serão simuladas mas não enviadas realmente')
"

# Verificar se modo emergência foi ativado
docker-compose logs web | grep -E "(EMERGÊNCIA|FALLBACK|SIMULAÇÃO)"
```

##  **Monitoramento de Performance**

```bash
# Ver uso de CPU/RAM dos containers
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Logs de performance
docker-compose logs web | grep -E "(INFO|ERROR|WARNING)" | tail -50

# Verificar conexões do banco
docker-compose exec db psql -U postgres -d csgo_skins -c "SELECT count(*) FROM pg_stat_activity;"
```

##  **Comandos por Ambiente**

###  **Desenvolvimento**
```bash
# Modo desenvolvimento com hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Debug com shell interativo
docker-compose run --rm web bash
```

###  **Produção**
```bash
# Deploy de produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verificar saúde em produção
docker-compose exec web curl -f http://localhost:5000/health
```

##  **Referências Rápidas**

###  **URLs Importantes**
- **Aplicação Web:** http://localhost:5000
- **Admin Panel:** http://localhost:5000/admin/login
- **PostgreSQL:** localhost:5432

###  **Credenciais Padrão**
- **Admin User:** admin
- **Admin Password:** admin123
- **DB User:** postgres
- **DB Password:** postgres
- **DB Name:** csgo_skins

###  **Tags de Containers**
- **Web Container:** `documentacaoflask---copia-web`
- **DB Container:** `documentacaoflask---copia-db`
- **Network:** `documentacaoflask---copia_default`

---

##  **Dicas Importantes**

1. ** Sempre faça backup** antes de comandos destrutivos
2. ** Monitore os logs** regularmente com `docker-compose logs -f`
3. ** Limpe recursos** periodicamente com `docker system prune`
4. ** Use cache** do Docker para builds mais rápidos
5. ** Verifique status** com `docker-compose ps` frequentemente

**Versão:** 2.0  
**Última Atualização:** 26 de Julho de 2025  
**Projeto:** TitoSkins - Plataforma CS2

---

##  **CHANGELOG v2.0 (26/07/2025)**

###  **Correções Implementadas**
- ** Autenticação Steam Robusta**: Sistema de retry com múltiplas tentativas de login
- ** Modo Fallback de Emergência**: Simulação de ofertas quando login Steam falha
- ** Performance Otimizada**: Timeouts progressivos e configurações de rede aprimoradas
- ** Sistema de Retry Inteligente**: 3 tentativas com configurações escaláveis
- ** Monitoramento Avançado**: Logs detalhados para diagnóstico de problemas

###  **Problemas Resolvidos**
-  `KeyError: access_token` - Corrigido com sistema de retry robusto
-  Falhas de autenticação Steam - Implementado fallback de emergência
-  Timeouts de conexão - Configurações progressivas de timeout
-  Conectividade de banco - Restart automático e verificação de saúde

###  **Melhorias Técnicas**
- **Autenticação Steam**: 3 níveis de configuração (30s → 60s → 120s timeout)
- **Headers HTTP**: User-Agent atualizado e headers robustos
- **Fallback Inteligente**: Validação via HTTP direto quando aiosteampy falha
- **Logs Estruturados**: Rastreamento completo de tentativas e erros
