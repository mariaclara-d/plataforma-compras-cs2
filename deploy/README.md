# 🚀 Deploy - Scripts e Configurações

Esta pasta contém tudo necessário para fazer deploy da aplicação.

## 📄 Arquivos Principais

### 🔧 Scripts de Deploy
- **`deploy_heroku.ps1`** - Script automatizado para Windows/PowerShell
- **`deploy_heroku.sh`** - Script automatizado para Linux/Mac
- **`CHECKLIST_DEPLOY.md`** - Guia completo passo-a-passo

## ⚡ Deploy Rápido

### Windows:
```powershell
.\deploy\deploy_heroku.ps1
```

### Linux/Mac:
```bash
chmod +x deploy/deploy_heroku.sh
./deploy/deploy_heroku.sh
```

## 📋 Checklist Completo

Siga o arquivo `CHECKLIST_DEPLOY.md` para um deploy detalhado com:
- ✅ Pré-requisitos
- ✅ Configuração Heroku
- ✅ Configuração de domínio
- ✅ Testes finais
- ✅ Planos B para problemas

## ⏱️ Tempo Estimado
- **Deploy básico:** 45 minutos
- **Deploy completo:** 4-6 horas
- **Propagação DNS:** 2-48 horas

## 🎯 Resultado Esperado
- Site funcionando em `https://sua-app.herokuapp.com`
- Admin acessível em `https://sua-app.herokuapp.com/admin/login`
- Domínio custom configurado (se aplicável)
