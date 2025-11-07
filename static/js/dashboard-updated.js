// Dashboard JavaScript - Versão Atualizada e Funcional v2.0

// Função para atualizar o resumo de vendas
function atualizarResumoVenda() {
    const selectedCheckboxes = document.querySelectorAll('.skin-checkbox:checked');
    const selectedCount = selectedCheckboxes.length;
    let totalValue = 0;

    // Calcular valor total dos itens selecionados
    selectedCheckboxes.forEach(checkbox => {
        const price = parseFloat(checkbox.dataset.price || 0);
        totalValue += price;
    });

    // Atualizar elementos do DOM
    const selectedCountElement = document.getElementById('selectedCount');
    const totalValueElement = document.getElementById('totalValue');
    const finalAmountElement = document.getElementById('finalAmount');
    const btnVender = document.getElementById('btnVender');
    const btnLimpar = document.getElementById('btnLimpar');

    if (selectedCountElement) selectedCountElement.textContent = selectedCount;
    if (totalValueElement) totalValueElement.textContent = `R$ ${totalValue.toFixed(2)}`;
    if (finalAmountElement) finalAmountElement.textContent = `R$ ${totalValue.toFixed(2)}`;

    // Habilitar/desabilitar botões baseado na seleção
    if (btnVender) {
        btnVender.disabled = selectedCount === 0;
    }
    
    if (btnLimpar) {
        btnLimpar.disabled = selectedCount === 0;
    }
}

// Função para limpar seleção
function limparSelecao() {
    const checkboxes = document.querySelectorAll('.skin-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    atualizarResumoVenda();
}

// Função para adicionar event listeners nos checkboxes
function inicializarCheckboxes() {
    const checkboxes = document.querySelectorAll('.skin-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', atualizarResumoVenda);
    });
}

// Função para mostrar/esconder overlay nos cards do inventário
function configurarOverlayCards() {
    const inventoryItems = document.querySelectorAll('.inventory-item');
    inventoryItems.forEach(item => {
        const checkbox = item.querySelector('.skin-checkbox');
        
        item.addEventListener('click', function(e) {
            // Não trigger se clicou diretamente no checkbox ou label
            if (e.target.classList.contains('skin-checkbox') || 
                e.target.classList.contains('checkbox-label') ||
                e.target.closest('.checkbox-label')) {
                return;
            }
            
            // Toggle do checkbox
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                atualizarResumoVenda();
            }
        });
    });
}

// Função para preparar dados de venda
function prepararDadosVenda() {
    const selectedItems = [];
    const checkboxes = document.querySelectorAll('.skin-checkbox:checked');
    
    checkboxes.forEach(checkbox => {
        // Obter informações adicionais do item do DOM
        const itemCard = checkbox.closest('.inventory-item');
        const itemName = itemCard.querySelector('.item-name')?.textContent || 
                        itemCard.querySelector('.card-title')?.textContent || 
                        checkbox.dataset.name || 'Item';
        
        selectedItems.push({
            assetid: checkbox.value,
            price: parseFloat(checkbox.dataset.price || 0),
            market_hash_name: itemName.trim()
        });
    });
    
    return selectedItems;
}

// Função principal de venda
function venderItens() {
    const selectedItems = prepararDadosVenda();
    const tradelink = document.getElementById('tradelink')?.value.trim();
    
    // Validações
    if (selectedItems.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Atenção',
            text: 'Selecione pelo menos um item para vender.',
            confirmButtonColor: '#00FFBF'
        });
        return;
    }
    
    if (!tradelink) {
        Swal.fire({
            icon: 'warning',
            title: 'Trade URL Necessária',
            text: 'Cole sua Trade URL do Steam antes de enviar a oferta.',
            confirmButtonColor: '#00FFBF'
        });
        return;
    }
    
    // Validar formato da trade URL
    const tradeLinkPattern = /^https:\/\/steamcommunity\.com\/tradeoffer\/new\/\?partner=\d+&token=[\w-]+$/;
    if (!tradeLinkPattern.test(tradelink)) {
        Swal.fire({
            icon: 'warning',
            title: 'Trade URL Inválida',
            text: 'Por favor, cole uma Trade URL válida do Steam.',
            confirmButtonColor: '#00FFBF'
        });
        return;
    }
    
    // Verificar se todos os itens têm AssetID válido
    const invalidItems = selectedItems.filter(item => !item.assetid || !item.assetid.toString().match(/^\d+$/));
    if (invalidItems.length > 0) {
        Swal.fire({
            icon: 'error',
            title: 'Itens Inválidos',
            text: 'Alguns itens selecionados não possuem ID válido. Recarregue a página e tente novamente.',
            confirmButtonColor: '#00FFBF'
        });
        return;
    }
    
    // Calcular valor total
    const totalValue = selectedItems.reduce((sum, item) => sum + item.price, 0);
    
    // Confirmação de venda
    Swal.fire({
        title: 'Confirmar Venda',
        html: `
            <div class="text-start">
                <p><strong>Itens selecionados:</strong> ${selectedItems.length}</p>
                <p><strong>Valor total:</strong> R$ ${totalValue.toFixed(2)}</p>
                <p><strong>Proteção:</strong> 7 dias</p>
                <hr>
                <p class="text-warning small"><i class="fas fa-exclamation-triangle"></i> A oferta será enviada através do aiosteampy.</p>
                <p class="text-muted small">Os itens ficarão em proteção por 7 dias antes de liberar o saldo para saque.</p>
            </div>
        `,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#00FFBF',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Enviar Oferta Real',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            processarVenda(selectedItems, tradelink);
        }
    });
}

// Função para processar a venda
function processarVenda(selectedItems, tradelink) {
    // Mostrar loading
    Swal.fire({
        title: 'Processando Venda...',
        text: 'Conectando com a Steam via aiosteampy e enviando oferta...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    try {
        // Coletar dados de pagamento do formulário
        const dadosPagamento = coletarDadosPagamento();
        
        // Preparar dados para envio - formato compatível com a rota real
        const vendaData = {
            itens: selectedItems.map(item => ({
                assetid: item.assetid,
                price: item.price,
                market_hash_name: item.market_hash_name || 'Item'
            })),
            tradelink: tradelink,
            pagamento: dadosPagamento,
            csrf_token: document.getElementById('csrf_token')?.value
        };
        
        // Enviar para a rota real de trade
        fetch('/trade/enviar-oferta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.getElementById('csrf_token')?.value
            },
            body: JSON.stringify(vendaData)
        })
        .then(response => response.json())
        .then(data => {
            Swal.close();
            
            if (data.message && data.offer_id) {
                // Sucesso - oferta enviada
                Swal.fire({
                    icon: 'success',
                    title: 'Oferta Enviada!',
                    html: `
                        <div class="text-start">
                            <p><strong> ${data.message}</strong></p>
                            <p><strong>ID da Oferta:</strong> ${data.offer_id}</p>
                            <p><strong>Itens:</strong> ${selectedItems.length} selecionados</p>
                            <p><strong>Status:</strong> Aguardando aceitação no Steam</p>
                            <p><strong>Pagamento:</strong> ${dadosPagamento.metodo_pagamento.toUpperCase()}</p>
                            ${data.trade_protection ? `
                                <hr>
                                <p><strong> Proteção Ativa:</strong> ${data.trade_protection.periodo_dias} dias</p>
                                <p class="text-muted small">${data.trade_protection.message}</p>
                            ` : ''}
                        </div>
                    `,
                    confirmButtonColor: '#00FFBF'
                }).then(() => {
                    // Limpar seleção
                    limparSelecao();
                    // Atualizar saldo
                    atualizarSaldo();
                    // Mostrar toast de sucesso
                    showSuccessToast('Oferta enviada com sucesso!');
                    // Notificar monitor de status sobre sucesso
                    if (window.steamStatusMonitor) {
                        window.steamStatusMonitor.onTradeSuccess();
                    }
                });
            } else if (data.error) {
                // Erro no processamento
                let errorTitle = 'Erro ao Enviar Oferta';
                let errorIcon = 'error';
                let showRetryButton = false;
                let retryTime = '';
                
                // Personalizar mensagem baseada no tipo de erro
                if (data.tipo === 'steam_server_error') {
                    errorIcon = 'warning';
                    errorTitle = ' Steam Temporariamente Indisponível';
                    showRetryButton = true;
                    retryTime = data.retry_sugestao || 'alguns minutos';
                } else if (data.tipo === 'rate_limit_error') {
                    errorIcon = 'warning';
                    errorTitle = '⏳ Limite de Tentativas Atingido';
                    showRetryButton = true;
                    retryTime = data.retry_sugestao || '30 minutos';
                } else if (data.tipo === 'timeout_error') {
                    errorIcon = 'warning';
                    errorTitle = '⏱ Timeout da Steam';
                    showRetryButton = true;
                    retryTime = data.retry_sugestao || '5 minutos';
                } else if (data.tipo === 'network_error') {
                    errorIcon = 'warning';
                    errorTitle = ' Problema de Conectividade';
                    showRetryButton = true;
                    retryTime = data.retry_sugestao || '2-5 minutos';
                } else if (data.tipo === 'steam_auth_error') {
                    errorTitle = ' Erro de Autenticação Steam';
                    errorIcon = 'warning';
                }
                
                let htmlContent = `
                    <div class="text-start">
                        <p><strong>${data.error}</strong></p>
                        ${data.details ? `<p class="text-muted">${data.details}</p>` : ''}
                        ${data.codigo_steam ? `<p class="text-muted small">Código Steam: ${data.codigo_steam}</p>` : ''}
                        ${showRetryButton ? `
                            <hr>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i> 
                                <strong>Sugestão:</strong> ${retryTime}
                            </div>
                        ` : ''}
                        ${data.contato_suporte ? `
                            <div class="alert alert-warning">
                                <i class="fas fa-headset"></i> 
                                Se o problema persistir, entre em contato com o suporte.
                            </div>
                        ` : ''}
                    </div>
                `;
                
                let swalConfig = {
                    icon: errorIcon,
                    title: errorTitle,
                    html: htmlContent,
                    confirmButtonColor: '#00FFBF',
                    confirmButtonText: 'Entendi'
                };
                
                // Adicionar botão de retry para erros temporários
                if (showRetryButton) {
                    swalConfig.showCancelButton = true;
                    swalConfig.cancelButtonColor = '#6c757d';
                    swalConfig.cancelButtonText = 'Tentar Novamente';
                    swalConfig.confirmButtonText = 'OK';
                    
                    // Notificar monitor de status sobre erro
                    if (window.steamStatusMonitor) {
                        window.steamStatusMonitor.onTradeError(data.tipo);
                    }
                    
                    Swal.fire(swalConfig).then((result) => {
                        if (result.isDismissed && result.dismiss === Swal.DismissReason.cancel) {
                            // Usuário clicou em "Tentar Novamente"
                            processarVenda(selectedItems, tradelink);
                        }
                    });
                } else {
                    // Notificar monitor de status sobre erro
                    if (window.steamStatusMonitor) {
                        window.steamStatusMonitor.onTradeError(data.tipo);
                    }
                    
                    Swal.fire(swalConfig);
                }
            }
        })
        .catch(error => {
            Swal.close();
            console.error('Erro na requisição:', error);
            
            Swal.fire({
                icon: 'error',
                title: 'Erro de Conexão',
                html: `
                    <div class="text-start">
                        <p><strong>Não foi possível conectar com o servidor.</strong></p>
                        <p class="text-muted">Verifique sua conexão e tente novamente.</p>
                    </div>
                `,
                confirmButtonColor: '#00FFBF'
            });
        });
        
    } catch (error) {
        Swal.close();
        
        Swal.fire({
            icon: 'warning',
            title: 'Dados de Pagamento Incompletos',
            text: error.message,
            confirmButtonColor: '#00FFBF'
        });
    }
}

// Função para mostrar toast de sucesso
function showSuccessToast(message) {
    // Criar elemento de toast se não existir
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        background: linear-gradient(45deg, #28a745, #00FFBF);
        color: #1C1A24;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 10px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 255, 191, 0.3);
        animation: slideIn 0.3s ease-out;
    `;
    toast.textContent = message;
    
    // Adicionar animação CSS
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
    
    toastContainer.appendChild(toast);
    
    // Remover após 3 segundos
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Função para atualizar saldo do usuário
function atualizarSaldo() {
    fetch('/api/saldo', {
        headers: {
            'X-CSRFToken': document.getElementById('csrf_token')?.value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && !data.error) {
            const saldoElements = document.querySelectorAll('#saldoAtual, #totalBalance');
            saldoElements.forEach(element => {
                if (element) {
                    element.textContent = data.saldo.toFixed(2);
                }
            });
        }
    })
    .catch(error => {
        console.error('Erro ao atualizar saldo:', error);
    });
}

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard JavaScript carregado');
    
    // Inicializar funcionalidades
    inicializarCheckboxes();
    configurarOverlayCards();
    atualizarResumoVenda();
    inicializarFormaPagamento();
    
    // Configurar botão de venda
    const btnVender = document.getElementById('btnVender');
    if (btnVender) {
        btnVender.addEventListener('click', venderItens);
    }
    
    // Configurar botão de limpar
    const btnLimpar = document.getElementById('btnLimpar');
    if (btnLimpar) {
        btnLimpar.addEventListener('click', limparSelecao);
    }
    
    // Atualizar saldo inicial
    atualizarSaldo();
    
    // Configurar tabs para carregar dados específicos
    const protectionTab = document.getElementById('protection-tab');
    if (protectionTab) {
        protectionTab.addEventListener('shown.bs.tab', loadTradeProtectionData);
    }
    
    const balanceTab = document.getElementById('balance-tab');
    if (balanceTab) {
        balanceTab.addEventListener('shown.bs.tab', loadBalanceData);
    }
});

// Função para inicializar forma de pagamento
function inicializarFormaPagamento() {
    const paymentMethodSelect = document.getElementById('paymentMethod');
    if (!paymentMethodSelect) return;
    
    // Configurar evento de mudança
    paymentMethodSelect.addEventListener('change', function() {
        mostrarCamposPagamento(this.value);
    });
    
    // Mostrar campos iniciais (PIX por padrão)
    mostrarCamposPagamento('pix');
}

// Função para mostrar/esconder campos de pagamento
function mostrarCamposPagamento(metodo) {
    const allFields = document.querySelectorAll('.payment-fields');
    
    // Esconder todos os campos
    allFields.forEach(field => {
        field.classList.add('d-none');
    });
    
    // Mostrar campos do método selecionado
    const targetField = document.getElementById(metodo + 'Fields');
    if (targetField) {
        targetField.classList.remove('d-none');
    }
}

// Função para coletar dados de pagamento
function coletarDadosPagamento() {
    const metodo = document.getElementById('paymentMethod')?.value || 'pix';
    const dadosPagamento = {
        metodo_pagamento: metodo
    };
    
    switch(metodo) {
        case 'pix':
            const pixKey = document.getElementById('pixKey')?.value.trim();
            if (!pixKey) {
                throw new Error('Chave PIX é obrigatória');
            }
            dadosPagamento.chave_pix = pixKey;
            break;
            
        case 'transfer':
            const banco = document.getElementById('bankName')?.value.trim();
            const agencia = document.getElementById('bankAgency')?.value.trim();
            const conta = document.getElementById('bankAccount')?.value.trim();
            const tipoConta = document.getElementById('accountType')?.value;
            
            if (!banco || !agencia || !conta) {
                throw new Error('Todos os dados bancários são obrigatórios');
            }
            
            dadosPagamento.banco = banco;
            dadosPagamento.agencia = agencia;
            dadosPagamento.conta = conta;
            dadosPagamento.tipo_conta = tipoConta;
            break;
            
        case 'skrill':
            const skrillEmail = document.getElementById('skrillEmail')?.value.trim();
            if (!skrillEmail) {
                throw new Error('E-mail Skrill é obrigatório');
            }
            dadosPagamento.carteira = skrillEmail;
            break;
    }
    
    return dadosPagamento;
}

// Função para carregar dados de proteção (mantida do código original)
function loadTradeProtectionData() {
    fetch('/api/trade-holds/info', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.getElementById('csrf_token')?.value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateProtectionBalances(data.balances || {total: 0, available: 0, protected: 0});
            renderActiveHolds(data.holds || []);
        } else {
            console.warn('Dados de proteção não disponíveis:', data.message);
            // Definir valores padrão se não houver dados
            updateProtectionBalances({total: 0, available: 0, protected: 0});
            renderActiveHolds([]);
        }
    })
    .catch(error => {
        console.error('Erro ao carregar dados de proteção:', error);
        // Definir valores padrão em caso de erro
        updateProtectionBalances({total: 0, available: 0, protected: 0});
        renderActiveHolds([]);
    });
}

// Função para atualizar saldos de proteção
function updateProtectionBalances(balances) {
    const elements = {
        totalBalance: document.getElementById('totalBalance'),
        availableBalance: document.getElementById('availableBalance'),
        protectedBalance: document.getElementById('protectedBalance'),
        withdrawableAmount: document.getElementById('withdrawableAmount')
    };
    
    if (elements.totalBalance) elements.totalBalance.textContent = `R$ ${balances.total.toFixed(2)}`;
    if (elements.availableBalance) elements.availableBalance.textContent = `R$ ${balances.available.toFixed(2)}`;
    if (elements.protectedBalance) elements.protectedBalance.textContent = `R$ ${balances.protected.toFixed(2)}`;
    if (elements.withdrawableAmount) elements.withdrawableAmount.textContent = `R$ ${balances.available.toFixed(2)}`;
}

// Função para renderizar holds ativos
function renderActiveHolds(holds) {
    const container = document.getElementById('holdsContainer');
    
    if (!container) return;
    
    if (!holds || holds.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhum trade em proteção no momento.</p>';
        return;
    }
    
    container.innerHTML = holds.map(hold => `
        <div class="card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-3">
                        <strong>Trade #${hold.id}</strong><br>
                        <small class="text-muted">${new Date(hold.created_at).toLocaleDateString('pt-BR')}</small>
                    </div>
                    <div class="col-md-2">
                        <h5 class="text-primary mb-0">R$ ${hold.amount.toFixed(2)}</h5>
                    </div>
                    <div class="col-md-3">
                        <div class="countdown" data-expires="${hold.expires_at}">
                            <small class="text-muted">Libera em:</small><br>
                            <span class="countdown-timer"></span>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <span class="badge bg-${hold.status === 'active' ? 'warning' : 'success'}">${hold.status}</span>
                    </div>
                    <div class="col-md-2">
                        ${hold.can_reverse ? `
                            <button class="btn btn-sm btn-outline-danger" onclick="reverseHold(${hold.id})">
                                <i class="fas fa-undo"></i> Reverter
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Função para carregar dados de saldo
function loadBalanceData() {
    fetch('/api/transactions/history', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.getElementById('csrf_token')?.value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            renderTransactionHistory(data.transactions || []);
        } else {
            console.warn('Histórico de transações não disponível:', data.message);
            renderTransactionHistory([]);
        }
    })
    .catch(error => {
        console.error('Erro ao carregar histórico:', error);
        renderTransactionHistory([]);
    });
}

// Função para renderizar histórico de transações
function renderTransactionHistory(transactions) {
    const container = document.getElementById('transactionHistory');
    
    if (!container) return;
    
    if (!transactions || transactions.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhuma transação encontrada.</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Tipo</th>
                        <th>Valor</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${transactions.map(tx => `
                        <tr>
                            <td>${new Date(tx.created_at).toLocaleDateString('pt-BR')}</td>
                            <td>${tx.type}</td>
                            <td>R$ ${tx.amount.toFixed(2)}</td>
                            <td><span class="badge bg-${tx.status === 'completed' ? 'success' : 'warning'}">${tx.status}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// Expor funções globalmente se necessário
window.venderItens = venderItens;
window.limparSelecao = limparSelecao;
window.atualizarResumoVenda = atualizarResumoVenda;
