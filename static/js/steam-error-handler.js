// Sistema de tratamento de erros Steam - TitoSkins
class SteamErrorHandler {
    constructor() {
        this.retryAttempts = 0;
        this.maxRetries = 2;
    }

    // Tratar resposta de erro do servidor
    handleTradeError(response, xhr) {
        const errorData = response;
        const errorType = errorData.tipo || 'general_error';
        
        switch(errorType) {
            case 'steam_server_error':
                this.showSteamServerError(errorData);
                break;
            case 'steam_auth_error':
                this.showAuthError(errorData);
                break;
            case 'rate_limit_error':
                this.showRateLimitError(errorData);
                break;
            default:
                this.showGeneralError(errorData);
                break;
        }
    }

    // Erro 500 da Steam - Servidores indisponíveis
    showSteamServerError(errorData) {
        Swal.fire({
            icon: 'warning',
            title: '⚠️ Steam Temporariamente Indisponível',
            html: `
                <div class="steam-error-content">
                    <p><strong>Os servidores da Steam estão com problemas.</strong></p>
                    <p>Isso é temporário e não é culpa nossa!</p>
                    <br>
                    <div class="error-actions">
                        <button class="btn btn-primary" onclick="steamErrorHandler.scheduleRetry()">
                            🔄 Tentar Novamente em 30s
                        </button>
                        <button class="btn btn-secondary" onclick="steamErrorHandler.checkSteamStatus()">
                            📊 Verificar Status da Steam
                        </button>
                    </div>
                </div>
            `,
            showConfirmButton: false,
            allowOutsideClick: false,
            timer: 30000,
            timerProgressBar: true
        });
    }

    // Erro de autenticação
    showAuthError(errorData) {
        Swal.fire({
            icon: 'error',
            title: '🔒 Problema de Autenticação',
            html: `
                <p>Nosso bot Steam está com problemas de autenticação.</p>
                <p><strong>Entre em contato com o suporte.</strong></p>
                <br>
                <button class="btn btn-primary" onclick="steamErrorHandler.contactSupport()">
                    💬 Contatar Suporte
                </button>
            `,
            showConfirmButton: false
        });
    }

    // Erro de rate limit
    showRateLimitError(errorData) {
        Swal.fire({
            icon: 'info',
            title: '⏳ Muitas Tentativas',
            html: `
                <p>Você fez muitas tentativas em pouco tempo.</p>
                <p><strong>Aguarde alguns minutos antes de tentar novamente.</strong></p>
                <br>
                <div class="countdown-timer">
                    Próxima tentativa em: <span id="countdown">300</span>s
                </div>
            `,
            showConfirmButton: false,
            timer: 300000, // 5 minutos
            timerProgressBar: true,
            didOpen: () => {
                this.startCountdown(300);
            }
        });
    }

    // Erro geral
    showGeneralError(errorData) {
        Swal.fire({
            icon: 'error',
            title: '❌ Erro Técnico',
            html: `
                <p>${errorData.detalhes || 'Erro desconhecido'}</p>
                <br>
                <button class="btn btn-primary" onclick="location.reload()">
                    🔄 Recarregar Página
                </button>
                <button class="btn btn-secondary" onclick="steamErrorHandler.contactSupport()">
                    💬 Reportar Erro
                </button>
            `,
            showConfirmButton: false
        });
    }

    // Agendar retry automático
    scheduleRetry() {
        Swal.fire({
            icon: 'info',
            title: '🔄 Tentando Novamente...',
            text: 'Aguarde enquanto tentamos enviar sua oferta novamente.',
            showConfirmButton: false,
            allowOutsideClick: false
        });

        // Tentar novamente após 5 segundos
        setTimeout(() => {
            this.retryTradeOffer();
        }, 5000);
    }

    // Retry da oferta
    retryTradeOffer() {
        if (this.retryAttempts >= this.maxRetries) {
            Swal.fire({
                icon: 'error',
                title: 'Máximo de Tentativas Excedido',
                text: 'Não foi possível enviar a oferta após várias tentativas. Contate o suporte.',
                showConfirmButton: true
            });
            return;
        }

        this.retryAttempts++;
        
        // Re-executar o último envio de oferta
        if (window.lastTradeData) {
            this.sendTradeOffer(window.lastTradeData);
        }
    }

    // Verificar status da Steam
    checkSteamStatus() {
        window.open('https://steamstat.us/', '_blank');
    }

    // Contatar suporte
    contactSupport() {
        window.open('https://wa.me/5574999619371?text=Preciso de ajuda com um erro na plataforma', '_blank');
    }

    // Countdown timer
    startCountdown(seconds) {
        const countdownElement = document.getElementById('countdown');
        if (!countdownElement) return;

        const interval = setInterval(() => {
            seconds--;
            countdownElement.textContent = seconds;
            
            if (seconds <= 0) {
                clearInterval(interval);
            }
        }, 1000);
    }

    // Integração com o sistema de envio de ofertas
    sendTradeOffer(tradeData) {
        // Salvar dados para retry
        window.lastTradeData = tradeData;
        
        // Mostrar loading
        Swal.fire({
            title: '🚀 Enviando Oferta...',
            text: 'Aguarde enquanto processamos sua solicitação.',
            allowOutsideClick: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        fetch('/trade/enviar-oferta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': tradeData.csrf_token
            },
            body: JSON.stringify(tradeData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                this.handleTradeError(data);
            } else if (data.success) {
                // Sucesso
                Swal.fire({
                    icon: 'success',
                    title: '✅ Oferta Enviada!',
                    html: `
                        <p><strong>Oferta criada com sucesso!</strong></p>
                        <p>ID da Oferta: <code>${data.offer_id || 'N/A'}</code></p>
                        <br>
                        <p class="text-muted">Verifique sua conta Steam para aceitar a trade offer.</p>
                    `,
                    showConfirmButton: true,
                    confirmButtonText: 'Entendi'
                });
                this.retryAttempts = 0; // Reset contador
            } else {
                // Resposta inesperada
                this.showGeneralError({
                    detalhes: data.message || 'Resposta inesperada do servidor'
                });
            }
        })
        .catch(error => {
            console.error('Erro na requisição:', error);
            this.showGeneralError({
                detalhes: 'Erro de conexão. Verifique sua internet e tente novamente.'
            });
        });
    }
}

// Instanciar globalmente
const steamErrorHandler = new SteamErrorHandler();

// CSS para melhorar a aparência dos erros
const steamErrorCSS = `
<style>
.steam-error-content {
    text-align: center;
    padding: 20px;
}

.error-actions {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
}

.countdown-timer {
    font-size: 18px;
    font-weight: bold;
    color: #007bff;
    margin: 15px 0;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    margin: 5px;
    text-decoration: none;
    display: inline-block;
}

.btn-primary {
    background-color: #007bff;
    color: white;
}

.btn-secondary {
    background-color: #6c757d;
    color: white;
}

.btn:hover {
    opacity: 0.8;
}
</style>
`;

// Injetar CSS
document.head.insertAdjacentHTML('beforeend', steamErrorCSS);
