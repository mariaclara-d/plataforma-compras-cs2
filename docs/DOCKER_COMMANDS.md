# 🐳 COMANDOS DOCKER E LOGS - GUIA COMPLETO

## 🚀 **INICIALIZAÇÃO**

### Iniciar containers em background
```bash
docker-compose up -d
```

### Verificar status
```bash
docker ps
```

### Parar containers
```bash
docker-compose down
```

## 📊 **ACOMPANHAR LOGS**

### 1. Logs da Aplicação Flask (container web)
```bash
# Logs em tempo real
docker-compose logs -f web

# Últimas 50 linhas
docker-compose logs --tail=50 web

# Logs com timestamp
docker-compose logs -f -t web
```

### 2. Logs do PostgreSQL (container db)
```bash
# Logs do banco em tempo real
docker-compose logs -f db

# Últimas 100 linhas do banco
docker-compose logs --tail=100 db
```

### 3. Logs de Todos os Containers
```bash
# Todos os logs em tempo real
docker-compose logs -f

# Logs específicos por tempo
docker-compose logs --since="1h" -f
```

### 4. Logs Diretos dos Containers
```bash
# Por nome do container
docker logs -f documentacaoflask---copia-web-1
docker logs -f documentacaoflask---copia-db-1

# Por ID do container (use docker ps para ver IDs)
docker logs -f b3300366c7f7
docker logs -f 285a15776182
```

## 📁 **LOGS DA APLICAÇÃO FLASK**

### Logs locais (fora do Docker)
```bash
# Log da aplicação
Get-Content logs\app.log -Wait

# Log de segurança  
Get-Content logs\security.log -Wait

# Log de erros
Get-Content logs\error.log -Wait

# Todos os logs
Get-Content logs\*.log -Wait
```

### No Linux/macOS seria:
```bash
tail -f logs/app.log
tail -f logs/security.log  
tail -f logs/error.log
```

## 🔍 **COMANDOS ÚTEIS DE DEBUG**

### Verificar configuração do container
```bash
docker-compose config
```

### Entrar no container Flask
```bash
docker-compose exec web bash
```

### Entrar no container PostgreSQL
```bash
docker-compose exec db psql -U postgres -d postgres
```

### Ver recursos usados
```bash
docker stats
```

### Reiniciar apenas um serviço
```bash
docker-compose restart web
docker-compose restart db
```

## 🎯 **COMANDOS MAIS USADOS NO DIA A DIA**

### Iniciar e acompanhar
```bash
# 1. Iniciar containers
docker-compose up -d

# 2. Acompanhar logs da aplicação
docker-compose logs -f web
```

### Para desenvolvimento ativo
```bash
# Terminal 1: Logs da aplicação
docker-compose logs -f web

# Terminal 2: Logs do banco (se necessário)
docker-compose logs -f db

# Terminal 3: Logs locais da aplicação
Get-Content logs\app.log -Wait
```

### Limpeza periódica
```bash
# Remover containers parados
docker container prune

# Remover imagens não usadas
docker image prune

# Limpeza completa (cuidado!)
docker system prune
```

## 🚨 **TROUBLESHOOTING**

### Container não inicia
```bash
# Ver logs de inicialização
docker-compose logs web
docker-compose logs db

# Verificar configuração
docker-compose config
```

### Problemas de porta
```bash
# Ver que processo usa a porta
netstat -an | findstr :5000
netstat -an | findstr :5432

# Matar processo na porta (se necessário)
taskkill /F /PID <PID>
```

### Reconstruir containers
```bash
# Reconstruir sem cache
docker-compose build --no-cache

# Recriar containers
docker-compose up -d --force-recreate
```

---

## 🎯 **RESUMO DOS COMANDOS ESSENCIAIS**

```bash
# Iniciar
docker-compose up -d

# Acompanhar logs da aplicação
docker-compose logs -f web

# Acompanhar logs do banco
docker-compose logs -f db

# Parar
docker-compose down

# Status
docker ps
```
