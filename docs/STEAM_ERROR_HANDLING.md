# Sistema de Tratamento de Erros Steam - TitoSkins

## Visão Geral
Implementamos um sistema robusto para tratar erros da API Steam durante o processo de envio de trade offers, oferecendo uma experiência mais amigável ao usuário e maior confiabilidade na plataforma.

## Componentes Implementados

### 1. Backend - Tratamento de Erros (`services/aiosteampy_service.py`)

#### Melhorias Adicionadas:
- **Categorização de Erros**: Diferentes tipos de erro são identificados e tratados de forma específica
- **Mensagens Personalizadas**: Cada tipo de erro possui uma mensagem clara para o usuário
- **Logging Detalhado**: Registros completos dos erros para diagnóstico

#### Tipos de Erro Tratados:
```python
# Erro 500 - Servidores Steam Indisponíveis
if e.response.status == 500:
    return {
        "erro": True,
        "tipo": "steam_server_error",
        "detalhes": "Steam servers temporarily unavailable"
    }

# Erro 403 - Problema de Autenticação
if e.response.status == 403:
    return {
        "erro": True,
        "tipo": "steam_auth_error", 
        "detalhes": "Authentication error with Steam"
    }

# Erro 429 - Rate Limit
if e.response.status == 429:
    return {
        "erro": True,
        "tipo": "rate_limit_error",
        "detalhes": "Rate limit exceeded"
    }
```

### 2. Backend - Sistema de Retry (`routes/trade.py`)

#### Funcionalidades:
- **Retry Automático**: 3 tentativas para erros temporários (500)
- **Backoff Exponencial**: Intervalos crescentes entre tentativas (5s, 10s, 15s)
- **Controle de Tentativas**: Contador de retry para evitar loops infinitos

#### Implementação:
```python
max_tentativas = 3
for tentativa_atual in range(1, max_tentativas + 1):
    try:
        resultado = await enviar_oferta_aiosteampy(client, tradelink, item_ids)
        
        if resultado.get("erro") and resultado.get("tipo") == "steam_server_error":
            if tentativa_atual < max_tentativas:
                delay = tentativa_atual * 5  # 5s, 10s, 15s
                await asyncio.sleep(delay)
                continue
        break
    except Exception as e:
        if tentativa_atual < max_tentativas:
            await asyncio.sleep(5)
            continue
        raise e
```

### 3. Frontend - Sistema de Alertas (`static/js/steam-error-handler.js`)

#### Características:
- **Alertas Visuais**: Interface moderna usando SweetAlert2
- **Retry Automático**: Botões para tentar novamente com delay visual
- **Feedback em Tempo Real**: Contadores e barras de progresso
- **Links Úteis**: Redirecionamento para status da Steam e suporte

#### Tipos de Alerta:

**1. Erro 500 - Steam Indisponível**
```javascript
showSteamServerError(errorData) {
    Swal.fire({
        icon: 'warning',
        title: '⚠️ Steam Temporariamente Indisponível',
        html: `
            <p><strong>Os servidores da Steam estão com problemas.</strong></p>
            <p>Isso é temporário e não é culpa nossa!</p>
            <button onclick="steamErrorHandler.scheduleRetry()">
                🔄 Tentar Novamente em 30s
            </button>
        `
    });
}
```

**2. Erro de Autenticação**
```javascript
showAuthError(errorData) {
    Swal.fire({
        icon: 'error',
        title: '🔒 Problema de Autenticação',
        html: `
            <p>Nosso bot Steam está com problemas de autenticação.</p>
            <button onclick="steamErrorHandler.contactSupport()">
                💬 Contatar Suporte
            </button>
        `
    });
}
```

**3. Rate Limit**
```javascript
showRateLimitError(errorData) {
    Swal.fire({
        icon: 'info',
        title: '⏳ Muitas Tentativas',
        html: `
            <p>Aguarde alguns minutos antes de tentar novamente.</p>
            <div class="countdown-timer">
                Próxima tentativa em: <span id="countdown">300</span>s
            </div>
        `,
        timer: 300000, // 5 minutos
    });
}
```

### 4. Template Updates (`templates/inventory.html`)

#### Integração Completa:
- **Herança do Base Template**: Uso consistente do layout da aplicação
- **Validação Frontend**: Verificação de itens selecionados antes do envio
- **Loading States**: Indicadores visuais durante o processamento
- **CSRF Protection**: Tokens de segurança integrados

```javascript
// Validação antes do envio
const itensSelecionados = document.querySelectorAll('input[name="item_ids"]:checked');
if (itensSelecionados.length === 0) {
    Swal.fire({
        icon: 'warning',
        title: 'Nenhum item selecionado',
        text: 'Por favor, selecione pelo menos um item para enviar na oferta.'
    });
    return;
}

// Uso do sistema de tratamento de erros
steamErrorHandler.sendTradeOffer(tradeData);
```

## Fluxo de Funcionamento

### 1. Envio de Oferta Normal
```
Usuário clica "Enviar Oferta"
↓
Frontend valida seleção
↓
Envia requisição via steamErrorHandler.sendTradeOffer()
↓
Backend tenta enviar via aiosteampy
↓
Sucesso: Exibe alerta de confirmação
```

### 2. Tratamento de Erro 500
```
Steam retorna erro 500
↓
Backend identifica como "steam_server_error"
↓
Executa retry automático (3x com delay)
↓
Se ainda falhar, retorna erro categorizado
↓
Frontend exibe alerta específico com opção de retry manual
```

### 3. Tratamento de Outros Erros
```
Steam retorna erro 403/429
↓
Backend categoriza o erro específico
↓
Retorna erro sem retry (não é temporário)
↓
Frontend exibe alerta adequado com ações específicas
```

## Benefícios da Implementação

### Para o Usuário:
- **Experiência Melhorada**: Alertas claros e informativos
- **Menos Frustração**: Entendimento do que está acontecendo
- **Ações Específicas**: Botões para resolver problemas
- **Retry Automático**: Sistema tenta resolver problemas sozinho

### Para o Sistema:
- **Maior Confiabilidade**: Retry automático para problemas temporários
- **Melhor Diagnóstico**: Logs detalhados para debugging
- **Escalabilidade**: Sistema preparado para diferentes tipos de erro
- **Manutenibilidade**: Código organizado e bem documentado

### Para a Operação:
- **Menos Suporte**: Usuários conseguem resolver problemas sozinhos
- **Visibilidade**: Logs ajudam a identificar padrões de erro
- **Professionalismo**: Interface polida e confiável

## Configurações e Customização

### Ajustar Tentativas de Retry:
```python
# Em routes/trade.py
max_tentativas = 3  # Alterar conforme necessário
delay = tentativa_atual * 5  # Ajustar delay entre tentativas
```

### Personalizar Mensagens:
```javascript
// Em steam-error-handler.js
title: '⚠️ Steam Temporariamente Indisponível'  // Personalizar títulos
text: 'Os servidores da Steam estão com problemas.'  // Personalizar textos
```

### Adicionar Novos Tipos de Erro:
1. Identificar no backend (`aiosteampy_service.py`)
2. Categorizar no endpoint (`routes/trade.py`)
3. Tratar no frontend (`steam-error-handler.js`)

## Monitoramento e Métricas

### Logs Importantes:
- Tentativas de retry executadas
- Tipos de erro mais frequentes
- Tempo de recuperação da Steam
- Taxa de sucesso após retry

### Alertas Recomendados:
- Alta taxa de erros 500 (problemas na Steam)
- Erros 403 recorrentes (problema de autenticação)
- Muitos rate limits (ajustar frequência)

## Próximos Passos

1. **Monitoramento**: Implementar dashboards para acompanhar métricas
2. **Notificações**: Sistema de alertas para admins quando há problemas
3. **Cache**: Implementar cache para reduzir chamadas à API Steam
4. **Fallback**: Sistema alternativo quando Steam está indisponível por muito tempo

---

**Versão**: 1.0  
**Data**: 24 de Janeiro de 2025  
**Autor**: Sistema TitoSkins  
**Status**: Implementado e Testado ✅
