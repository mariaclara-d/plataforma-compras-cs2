/**
 * Monitor de Status da Steam
 * Monitora a saúde dos servidores Steam e informa ao usuário
 */

class SteamStatusMonitor {
    constructor() {
        this.statusCache = {
            lastCheck: 0,
            status: 'unknown',
            ttl: 300000 // 5 minutos
        };
        this.init();
    }

    init() {
        this.createStatusIndicator();
        this.checkSteamStatus();
        
        // Verificar status a cada 5 minutos
        setInterval(() => {
            this.checkSteamStatus();
        }, 300000);
    }

    createStatusIndicator() {
        // Criar indicador de status na página
        const statusHtml = `
            <div id="steam-status-indicator" class="steam-status-indicator d-none">
                <div class="steam-status-content">
                    <i id="steam-status-icon" class="fas fa-circle"></i>
                    <span id="steam-status-text">Verificando Steam...</span>
                    <button id="steam-status-close" class="btn-close" type="button">×</button>
                </div>
            </div>
        `;

        // Adicionar CSS
        const style = document.createElement('style');
        style.textContent = `
            .steam-status-indicator {
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 1050;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                max-width: 350px;
                animation: slideInRight 0.3s ease-out;
            }

            .steam-status-content {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .steam-status-indicator .btn-close {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                margin-left: auto;
                cursor: pointer;
                opacity: 0.7;
            }

            .steam-status-indicator .btn-close:hover {
                opacity: 1;
            }

            .steam-status-indicator.status-ok .fa-circle {
                color: #28a745;
                animation: pulse 2s infinite;
            }

            .steam-status-indicator.status-warning .fa-circle {
                color: #ffc107;
                animation: pulse 2s infinite;
            }

            .steam-status-indicator.status-error .fa-circle {
                color: #dc3545;
                animation: pulse 2s infinite;
            }

            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        `;

        document.head.appendChild(style);
        document.body.insertAdjacentHTML('beforeend', statusHtml);

        // Event listeners
        document.getElementById('steam-status-close').addEventListener('click', () => {
            this.hideStatusIndicator();
        });
    }

    async checkSteamStatus() {
        const now = Date.now();
        
        // Usar cache se ainda válido
        if (now - this.statusCache.lastCheck < this.statusCache.ttl) {
            return this.statusCache.status;
        }

        try {
            // Tentar verificar status via nossa API
            const response = await fetch('/api/steam/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            let status = 'unknown';
            
            if (response.ok) {
                const data = await response.json();
                status = data.status || 'unknown';
            } else if (response.status === 503) {
                status = 'degraded';
            } else if (response.status >= 500) {
                status = 'error';
            }

            this.updateStatus(status);
            this.statusCache = {
                lastCheck: now,
                status: status,
                ttl: 300000
            };

            return status;

        } catch (error) {
            console.warn('Erro ao verificar status da Steam:', error);
            this.updateStatus('unknown');
            return 'unknown';
        }
    }

    updateStatus(status) {
        const indicator = document.getElementById('steam-status-indicator');
        const icon = document.getElementById('steam-status-icon');
        const text = document.getElementById('steam-status-text');

        if (!indicator || !icon || !text) return;

        // Remover classes anteriores
        indicator.classList.remove('status-ok', 'status-warning', 'status-error');

        switch (status) {
            case 'ok':
                indicator.classList.add('status-ok');
                text.textContent = 'Steam Online - Funcionando normalmente';
                this.hideStatusIndicator(3000); // Auto-hide após 3s
                break;

            case 'degraded':
                indicator.classList.add('status-warning');
                text.textContent = 'Steam com Instabilidade - Possíveis atrasos';
                this.showStatusIndicator();
                break;

            case 'error':
                indicator.classList.add('status-error');
                text.textContent = 'Steam com Problemas - Aguarde alguns minutos';
                this.showStatusIndicator();
                break;

            case 'maintenance':
                indicator.classList.add('status-warning');
                text.textContent = 'Steam em Manutenção - Tente mais tarde';
                this.showStatusIndicator();
                break;

            default:
                indicator.classList.add('status-warning');
                text.textContent = 'Status da Steam desconhecido';
                break;
        }
    }

    showStatusIndicator() {
        const indicator = document.getElementById('steam-status-indicator');
        if (indicator) {
            indicator.classList.remove('d-none');
        }
    }

    hideStatusIndicator(delay = 0) {
        const indicator = document.getElementById('steam-status-indicator');
        if (indicator) {
            if (delay > 0) {
                setTimeout(() => {
                    indicator.classList.add('d-none');
                }, delay);
            } else {
                indicator.classList.add('d-none');
            }
        }
    }

    // Método para ser chamado quando há erro de trade
    onTradeError(errorType) {
        if (errorType === 'steam_server_error') {
            this.updateStatus('error');
        } else if (errorType === 'rate_limit_error') {
            this.updateStatus('degraded');
        }
    }

    // Método para ser chamado quando trade tem sucesso
    onTradeSuccess() {
        this.updateStatus('ok');
    }
}

// Instanciar monitor quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    window.steamStatusMonitor = new SteamStatusMonitor();
});

// Exportar para uso em outros scripts
window.SteamStatusMonitor = SteamStatusMonitor;
