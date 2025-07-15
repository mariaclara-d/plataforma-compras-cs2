function selectPayment(method) {
    const paymentFields = document.getElementById("paymentFields");
    paymentFields.innerHTML = "";
    if (method === "pix") {
        paymentFields.innerHTML = `
            <label for="pixKey">Chave Pix:</label>
            <input type="text" id="pixKey" class="form-control" placeholder="E-mail, CPF, CNPJ ou Telefone" required>
        `;
    } else if (method === "transfer") {
        paymentFields.innerHTML = `
            <label for="bank">Banco:</label>
            <input type="text" id="bank" class="form-control" placeholder="Nome do banco" required />
            <label for="agency">Agência:</label>
            <input type="text" id="agency" class="form-control" placeholder="Número da agência" required />
            <label for="account">Conta:</label>
            <input type="text" id="account" class="form-control" placeholder="Número da conta" required />
            <label for="accountType">Tipo de Conta:</label>
            <select id="accountType" class="form-select" required>
                <option value="corrente">Corrente</option>
                <option value="poupanca">Poupança</option>
            </select>
        `;
    } else if (method === "skrill") {
        paymentFields.innerHTML = `
            <label for="email">E-mail Skrill:</label>
            <input type="email" id="email" class="form-control" placeholder="Digite seu e-mail" required>
        `;
    }
}

// Função para mostrar mensagens de forma amigável usando Bootstrap Modal
function showMessage(title, message, isError = false) {
    let modal = document.getElementById('feedbackModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'feedbackModal';
        modal.tabIndex = -1;
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"></h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body"></div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    modal.querySelector('.modal-title').textContent = title;
    modal.querySelector('.modal-body').textContent = message;
    if (isError) {
        modal.querySelector('.modal-header').classList.add('bg-danger', 'text-white');
    } else {
        modal.querySelector('.modal-header').classList.remove('bg-danger', 'text-white');
    }
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function atualizarSaldo() {
    fetch('/api/saldo')
        .then(response => response.json())
        .then(data => {
            if (!data.erro) {
                document.getElementById('saldoAtual').textContent = data.saldo.toFixed(2);
            } else {
                console.error(data.erro);
            }
        })
        .catch(error => console.error('Erro ao atualizar saldo:', error));
}

document.addEventListener("DOMContentLoaded", function () {
    const tradeLinkInput = document.getElementById("tradelink");
    const btnVender = document.getElementById("btnVender");
    function verificarExibicaoBotao() {
        const algumItemSelecionado = document.querySelector(".skin-checkbox:checked");
        if (tradeLinkInput.value.trim() && algumItemSelecionado) {
            btnVender.style.display = "block";
        } else {
            btnVender.style.display = "none";
        }
    }
    tradeLinkInput.addEventListener("input", verificarExibicaoBotao);
    document.querySelectorAll(".skin-checkbox").forEach((checkbox) =>
        checkbox.addEventListener("change", verificarExibicaoBotao)
    );
    // Atualiza o valor total ao carregar
    document.querySelectorAll('.skin-checkbox').forEach(cb => {
        cb.addEventListener('change', atualizarTotal);
    });
    atualizarTotal();
});

// Função separada para atualizar o valor total (sem comissão)
function atualizarTotal() {
    let total = 0;
    document.querySelectorAll('.skin-checkbox:checked').forEach(selected => {
        const preco = parseFloat(selected.dataset.price || 0);
        total += preco;
    });
    document.getElementById('totalAmount').textContent = `R$ ${total.toFixed(2)}`;
}

function enviarOferta() {
    const selectedItems = Array.from(document.querySelectorAll('.skin-checkbox:checked')).map(checkbox => ({
        assetid: checkbox.dataset.assetid
    }));
    const tradelink = document.getElementById('tradelink').value.trim();
    if (selectedItems.length === 0) {
        showMessage('Atenção', 'Selecione ao menos um item.', true);
        return;
    }
    if (!tradelink) {
        showMessage('Atenção', 'Cole sua Trade URL antes de enviar a oferta.', true);
        return;
    }
    let pagamento = {};
    const pixKey = document.getElementById("pixKey");
    const bank = document.getElementById("bank");
    const email = document.getElementById("email");
    if (pixKey) {
        pagamento.metodo_pagamento = "pix";
        pagamento.chave_pix = pixKey.value.trim();
        if (!pagamento.chave_pix) {
            showMessage('Atenção', 'Digite uma chave Pix válida.', true);
            return;
        }
    } else if (bank) {
        pagamento.metodo_pagamento = "transfer";
        pagamento.banco = bank.value.trim();
        pagamento.agencia = document.getElementById("agency").value.trim();
        pagamento.conta = document.getElementById("account").value.trim();
        pagamento.tipo_conta = document.getElementById("accountType").value;
        if (!pagamento.banco || !pagamento.agencia || !pagamento.conta) {
            showMessage('Atenção', 'Preencha todos os campos de transferência bancária.', true);
            return;
        }
    } else if (email) {
        pagamento.metodo_pagamento = "skrill";
        pagamento.carteira = email.value.trim();
        if (!pagamento.carteira.includes("@")) {
            showMessage('Atenção', 'Digite um e-mail válido para Skrill.', true);
            return;
        }
    } else {
        showMessage('Atenção', 'Escolha uma forma de pagamento.', true);
        return;
    }

    // Adiciona CSRF token ao body (importante para segurança)
    const csrfToken = window.csrfToken || "";

    // Mostra spinner de carregamento
    const btnVender = document.getElementById("btnVender");
    btnVender.disabled = true;
    btnVender.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...';

    fetch('/trade/enviar-oferta', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            itens: selectedItems,
            tradelink: tradelink,
            pagamento: pagamento,
            csrf_token: csrfToken
        })
    })
    .then(async response => {
        let data;
        try {
            data = await response.json();
        } catch (e) {
            showMessage('Erro', 'Erro inesperado no servidor. Tente novamente.', true);
            btnVender.disabled = false;
            btnVender.innerHTML = 'Vender';
            return;
        }
        btnVender.disabled = false;
        btnVender.innerHTML = 'Vender';
        if (data && typeof data.erro !== "undefined") {
            showMessage('Atenção', data.erro || 'Erro desconhecido.', true);
        } else {
            showMessage('Erro', 'Resposta inesperada do servidor.', true);
        }
    })
    .catch(error => {
        btnVender.disabled = false;
        btnVender.innerHTML = 'Vender';
        console.error("Erro ao enviar:", error);
        showMessage('Erro', '❌ Erro inesperado. Verifique o console.', true);
    });
}