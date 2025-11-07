/**
 * Trade Protection System - JavaScript Frontend
 * Sistema de proteção de 7 dias para trades
 */

class TradeProtectionManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupWithdrawValidation();
        this.loadUserHoldInfo();
        this.setupEventListeners();
    }

    /**
     * Validação de saque com verificação de trade holds
     */
    setupWithdrawValidation() {
        // Intercepta formulários de saque
        const withdrawForms = document.querySelectorAll('form[action*="saque"], .saque-form');
        withdrawForms.forEach(form => {
            form.addEventListener('submit', (e) => this.validateWithdraw(e));
        });

        // Intercepta botões de saque
        const withdrawButtons = document.querySelectorAll('.btn-saque, [data-action="withdraw"]');
        withdrawButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleWithdrawClick(e));
        });
    }

    /**
     * Valida se o saque pode ser realizado
     */
    async validateWithdraw(event) {
        const form = event.target;
        const valorInput = form.querySelector('input[name="valor"], #valor-saque');
        
        if (!valorInput) return; // Se não encontrar input de valor, deixa prosseguir

        const valor = parseFloat(valorInput.value);
        if (!valor || valor <= 0) return;

        event.preventDefault(); // Para o envio do formulário

        try {
            // Verifica saldo disponível
            const balanceInfo = await this.getBalanceInfo();
            
            if (balanceInfo && balanceInfo.balance) {
                const { saldo_disponivel, valor_em_hold } = balanceInfo.balance;
                
                if (valor > saldo_disponivel) {
                    this.showTradeProtectionModal(balanceInfo.balance, valor);
                    return;
                }
            }

            // Se chegou até aqui, pode prosseguir com o saque
            form.submit();
            
        } catch (error) {
            console.error('Erro ao validar saque:', error);
            // Em caso de erro, deixa prosseguir normalmente
            form.submit();
        }
    }

    /**
     * Manipula clique em botões de saque
     */
    async handleWithdrawClick(event) {
        const button = event.target;
        const valor = button.getAttribute('data-valor');
        
        if (!valor) return;

        event.preventDefault();

        try {
            const balanceInfo = await this.getBalanceInfo();
            
            if (balanceInfo && balanceInfo.balance) {
                const { saldo_disponivel } = balanceInfo.balance;
                
                if (parseFloat(valor) > saldo_disponivel) {
                    this.showTradeProtectionModal(balanceInfo.balance, parseFloat(valor));
                    return;
                }
            }

            // Prosseguir com a ação de saque
            this.processSaque(valor);
            
        } catch (error) {
            console.error('Erro ao processar saque:', error);
        }
    }

    /**
     * Obtém informações de saldo do usuário
     */
    async getBalanceInfo() {
        try {
            const response = await fetch('/api/trade-holds/balance', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.error('Erro ao obter informações de saldo:', error);
            return null;
        }
    }

    /**
     * Carrega informações dos holds do usuário
     */
    async loadUserHoldInfo() {
        try {
            const response = await fetch('/api/trade-holds/info');
            if (response.ok) {
                const holdInfo = await response.json();
                this.updateUI(holdInfo.data);
            }
        } catch (error) {
            console.error('Erro ao carregar holds:', error);
        }
    }

    /**
     * Atualiza a interface com informações de hold
     */
    updateUI(holdInfo) {
        if (!holdInfo) return;

        // Atualiza indicadores de saldo
        this.updateBalanceIndicators(holdInfo.balance_info);
        
        // Mostra notificação se houver holds ativos
        if (holdInfo.has_active_holds) {
            this.showHoldNotification(holdInfo);
        }
    }

    /**
     * Atualiza indicadores de saldo na interface
     */
    updateBalanceIndicators(balanceInfo) {
        if (!balanceInfo) return;

        // Atualiza saldo total
        const totalElements = document.querySelectorAll('.saldo-total, [data-balance="total"]');
        totalElements.forEach(el => {
            el.textContent = `R$ ${balanceInfo.saldo_total.toFixed(2)}`;
        });

        // Atualiza saldo disponível
        const availableElements = document.querySelectorAll('.saldo-disponivel, [data-balance="available"]');
        availableElements.forEach(el => {
            el.textContent = `R$ ${balanceInfo.saldo_disponivel.toFixed(2)}`;
        });

        // Atualiza valor em hold
        const holdElements = document.querySelectorAll('.valor-em-hold, [data-balance="hold"]');
        holdElements.forEach(el => {
            el.textContent = `R$ ${balanceInfo.valor_em_hold.toFixed(2)}`;
        });
    }

    /**
     * Mostra modal de Trade Protection quando saque é bloqueado
     */
    showTradeProtectionModal(balanceInfo, valorSolicitado) {
        const modalHtml = `
        <div class="modal fade" id="tradeProtectionModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fas fa-shield-alt"></i> Trade Protection Ativo
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <strong>Saque Limitado!</strong> Você possui valores em período de proteção.
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <div class="text-center p-3 bg-light rounded">
                                    <h6>Saldo Total</h6>
                                    <h4 class="text-primary">R$ ${balanceInfo.saldo_total.toFixed(2)}</h4>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="text-center p-3 bg-warning rounded">
                                    <h6>Em Proteção</h6>
                                    <h4 class="text-dark">R$ ${balanceInfo.valor_em_hold.toFixed(2)}</h4>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="text-center p-3 bg-success rounded">
                                    <h6>Disponível</h6>
                                    <h4 class="text-white">R$ ${balanceInfo.saldo_disponivel.toFixed(2)}</h4>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <strong>Valor solicitado:</strong> R$ ${valorSolicitado.toFixed(2)}<br>
                            <strong>Valor disponível:</strong> R$ ${balanceInfo.saldo_disponivel.toFixed(2)}
                        </div>
                        
                        <div class="bg-info p-3 rounded">
                            <h6><i class="fas fa-info-circle"></i> Como funciona a proteção?</h6>
                            <ul class="mb-0">
                                <li>Valores de vendas recentes ficam protegidos por 7 dias</li>
                                <li>Durante esse período, você pode reverter a venda</li>
                                <li>Apenas valores não protegidos podem ser sacados</li>
                                <li>Após 7 dias, o valor fica disponível automaticamente</li>
                            </ul>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            Entendi
                        </button>
                        <a href="/trade-protection" class="btn btn-primary">
                            <i class="fas fa-shield-alt"></i> Ver Itens Protegidos
                        </a>
                        ${balanceInfo.saldo_disponivel > 0 ? `
                        <button type="button" class="btn btn-success" onclick="tradeProtection.adjustWithdrawAmount(${balanceInfo.saldo_disponivel})">
                            Sacar R$ ${balanceInfo.saldo_disponivel.toFixed(2)}
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
        `;

        // Remove modal anterior se existir
        const existingModal = document.getElementById('tradeProtectionModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Adiciona novo modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Mostra o modal
        const modal = new bootstrap.Modal(document.getElementById('tradeProtectionModal'));
        modal.show();
    }

    /**
     * Ajusta o valor de saque para o máximo disponível
     */
    adjustWithdrawAmount(maxAmount) {
        const valorInputs = document.querySelectorAll('input[name="valor"], #valor-saque');
        valorInputs.forEach(input => {
            input.value = maxAmount.toFixed(2);
        });

        // Fecha o modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('tradeProtectionModal'));
        if (modal) {
            modal.hide();
        }
    }

    /**
     * Mostra notificação discreta sobre holds ativos
     */
    showHoldNotification(holdInfo) {
        if (!holdInfo.has_active_holds) return;

        const notification = `
        <div class="alert alert-info alert-dismissible fade show" role="alert" id="holdNotification">
            <i class="fas fa-shield-alt"></i>
            <strong>Trade Protection Ativo:</strong> 
            Você possui ${holdInfo.active_holds.length} item(ns) em proteção.
            <a href="/trade-protection" class="alert-link">Ver detalhes</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        `;

        // Adiciona no topo da página se não existir
        if (!document.getElementById('holdNotification')) {
            const container = document.querySelector('.container, .container-fluid, main, body');
            if (container) {
                container.insertAdjacentHTML('afterbegin', notification);
            }
        }
    }

    /**
     * Processa o saque (implementar conforme sua lógica)
     */
    processSaque(valor) {
        // Implementar a lógica de saque específica da aplicação
        console.log(`Processando saque de R$ ${valor}`);
        
        // Exemplo: submeter formulário ou fazer requisição AJAX
        const form = document.querySelector('form[action*="saque"], .saque-form');
        if (form) {
            form.submit();
        }
    }

    /**
     * Setup de event listeners adicionais
     */
    setupEventListeners() {
        // Atualizar informações periodicamente
        setInterval(() => {
            this.loadUserHoldInfo();
        }, 30000); // A cada 30 segundos

        // Listener para mudanças no input de valor
        const valorInputs = document.querySelectorAll('input[name="valor"], #valor-saque');
        valorInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                this.validateAmountInput(e.target);
            });
        });
    }

    /**
     * Valida input de valor em tempo real
     */
    async validateAmountInput(input) {
        const valor = parseFloat(input.value);
        if (!valor || valor <= 0) return;

        try {
            const balanceInfo = await this.getBalanceInfo();
            if (balanceInfo && balanceInfo.balance) {
                const { saldo_disponivel } = balanceInfo.balance;
                
                // Adiciona classe de aviso se valor exceder o disponível
                if (valor > saldo_disponivel) {
                    input.classList.add('is-invalid');
                    this.showInputWarning(input, saldo_disponivel);
                } else {
                    input.classList.remove('is-invalid');
                    this.hideInputWarning(input);
                }
            }
        } catch (error) {
            console.error('Erro ao validar valor:', error);
        }
    }

    /**
     * Mostra aviso no input
     */
    showInputWarning(input, maxAmount) {
        let warning = input.parentNode.querySelector('.trade-hold-warning');
        if (!warning) {
            warning = document.createElement('div');
            warning.className = 'trade-hold-warning text-warning small mt-1';
            input.parentNode.appendChild(warning);
        }
        warning.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Máximo disponível: R$ ${maxAmount.toFixed(2)}`;
    }

    /**
     * Esconde aviso do input
     */
    hideInputWarning(input) {
        const warning = input.parentNode.querySelector('.trade-hold-warning');
        if (warning) {
            warning.remove();
        }
    }
}

// Inicializa o sistema quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    window.tradeProtection = new TradeProtectionManager();
});

// Funções globais para uso em templates
window.TradeProtectionUtils = {
    formatCurrency: (value) => `R$ ${parseFloat(value).toFixed(2)}`,
    
    showHoldDetails: (holdId) => {
        fetch(`/api/trade-holds/info`)
            .then(response => response.json())
            .then(data => {
                console.log('Hold details:', data);
                // Implementar modal de detalhes se necessário
            });
    },
    
    checkWithdrawLimit: async (amount) => {
        try {
            const response = await fetch('/api/trade-holds/balance');
            const data = await response.json();
            return data.balance.saldo_disponivel >= amount;
        } catch (error) {
            console.error('Erro ao verificar limite:', error);
            return true; // Em caso de erro, permite prosseguir
        }
    }
};
