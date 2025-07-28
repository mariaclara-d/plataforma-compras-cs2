/**
 * Trade Success Handler - Manipula sucesso de vendas com Trade Protection
 */

class TradeSuccessHandler {
    
    /**
     * Mostra modal de sucesso da venda com informações de Trade Protection
     */
    static showTradeSuccessModal(response) {
        const { offer_id, trade_protection, mensagem } = response;
        
        let protectionInfo = '';
        if (trade_protection && trade_protection.ativo) {
            const holdInfo = trade_protection.hold_info;
            protectionInfo = `
            <div class="alert alert-info mt-3">
                <h6><i class="fas fa-shield-alt"></i> Trade Protection Ativado</h6>
                <p class="mb-2">${trade_protection.mensagem}</p>
                ${holdInfo ? `
                <div class="row text-center mt-2">
                    <div class="col-4">
                        <small class="text-muted">Em Proteção</small><br>
                        <strong>R$ ${holdInfo.total_em_hold.toFixed(2)}</strong>
                    </div>
                    <div class="col-4">
                        <small class="text-muted">Disponível</small><br>
                        <strong class="text-success">R$ ${holdInfo.saldo_disponivel.toFixed(2)}</strong>
                    </div>
                    <div class="col-4">
                        <small class="text-muted">Holds Ativos</small><br>
                        <strong>${holdInfo.holds_ativos}</strong>
                    </div>
                </div>
                ` : ''}
            </div>
            `;
        }

        Swal.fire({
            icon: 'success',
            title: '🎉 Venda Realizada!',
            html: `
                <div class="text-center">
                    <p class="lead">${mensagem}</p>
                    <div class="badge bg-primary fs-6 mb-3">
                        Oferta ID: ${offer_id}
                    </div>
                    ${protectionInfo}
                </div>
            `,
            confirmButtonText: 'Continuar',
            showCancelButton: trade_protection?.ativo,
            cancelButtonText: trade_protection?.ativo ? 'Ver Proteções' : null,
            confirmButtonColor: '#28a745',
            cancelButtonColor: '#007bff',
            allowOutsideClick: false,
            customClass: {
                popup: 'trade-success-modal',
                title: 'trade-success-title'
            }
        }).then((result) => {
            if (result.dismiss === Swal.DismissReason.cancel) {
                // Usuário clicou em "Ver Proteções"
                window.location.href = '/trade-protection';
            } else {
                // Usuário clicou em "Continuar"
                this.refreshUserInterface();
            }
        });
    }

    /**
     * Mostra modal de erro personalizado para problemas de Trade
     */
    static showTradeErrorModal(error) {
        let iconType = 'error';
        let title = 'Erro na Venda';
        let confirmButtonColor = '#dc3545';

        // Personalizar baseado no tipo de erro
        if (error.tipo === 'steam_server_error') {
            iconType = 'warning';
            title = 'Servidores Steam Indisponíveis';
            confirmButtonColor = '#ffc107';
        } else if (error.tipo === 'rate_limit_error') {
            iconType = 'info';
            title = 'Aguarde um Momento';
            confirmButtonColor = '#17a2b8';
        }

        Swal.fire({
            icon: iconType,
            title: title,
            html: `
                <div class="text-center">
                    <p class="lead">${error.erro}</p>
                    ${error.detalhes ? `<p class="text-muted">${error.detalhes}</p>` : ''}
                </div>
            `,
            confirmButtonText: 'Entendi',
            confirmButtonColor: confirmButtonColor,
            customClass: {
                popup: 'trade-error-modal'
            }
        });
    }

    /**
     * Atualiza a interface do usuário após uma venda bem-sucedida
     */
    static refreshUserInterface() {
        // Recarregar informações de saldo
        if (window.tradeProtection) {
            window.tradeProtection.loadUserHoldInfo();
        }

        // Atualizar outros elementos da interface conforme necessário
        // Exemplo: recarregar inventário, atualizar saldo na navbar, etc.
        
        // Se estiver na página de inventário, recarregar
        if (window.location.pathname.includes('inventory') || window.location.pathname.includes('market')) {
            setTimeout(() => {
                location.reload();
            }, 2000);
        }
    }

    /**
     * Intercepta respostas de sucesso de trade para mostrar modal
     */
    static setupTradeResponseInterceptor() {
        // Interceptar requisições de trade
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            return originalFetch.apply(this, args)
                .then(response => {
                    // Verificar se é uma resposta de trade
                    if (args[0] && args[0].includes('/trade/enviar-oferta')) {
                        return response.clone().json().then(data => {
                            if (response.ok && data.offer_id) {
                                // Sucesso na venda
                                TradeSuccessHandler.showTradeSuccessModal(data);
                            } else if (!response.ok && data.erro) {
                                // Erro na venda
                                TradeSuccessHandler.showTradeErrorModal(data);
                            }
                            return response;
                        }).catch(() => response);
                    }
                    return response;
                });
        };
    }
}

// CSS customizado para os modais
const tradeModalStyles = `
<style>
.trade-success-modal {
    border-radius: 15px !important;
}

.trade-success-title {
    color: #28a745 !important;
}

.trade-error-modal {
    border-radius: 15px !important;
}

.swal2-popup .badge {
    display: inline-block !important;
}

.swal2-popup .alert {
    text-align: left !important;
}

.swal2-popup .row {
    margin: 0 !important;
}

.swal2-popup .col-4 {
    padding: 0.5rem !important;
}
</style>
`;

// Adicionar estilos na página
document.addEventListener('DOMContentLoaded', function() {
    document.head.insertAdjacentHTML('beforeend', tradeModalStyles);
    TradeSuccessHandler.setupTradeResponseInterceptor();
});

// Exportar para uso global
window.TradeSuccessHandler = TradeSuccessHandler;
