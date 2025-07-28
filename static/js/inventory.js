document.getElementById("ofertaForm").addEventListener("submit", function (event) {
        event.preventDefault(); // Impede o envio padrão do formulário

        const tradelink = document.querySelector('input[name="tradelink"]').value;
        const csrfToken = document.getElementById('csrf_token').value;
        const btnEnviar = document.getElementById('btnEnviar');

        // Coletar itens selecionados
        const itens = Array.from(
            document.querySelectorAll('input[name="item_ids"]:checked')
        ).map(input => ({ assetid: input.value, appid: "730" }));

        // Validação básica no frontend
        if (!tradelink || itens.length === 0) {
            showStatus("Por favor, insira um tradelink válido e selecione ao menos um item.", "danger");
            return;
        }

        btnEnviar.disabled = true;
        btnEnviar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...';

        fetch("/trade/enviar-oferta", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ itens, tradelink, csrf_token: csrfToken }),
        })
        .then(async response => {
            let data;
            try {
                data = await response.json();
            } catch (e) {
                showStatus("Erro inesperado no servidor. Tente novamente.", "danger");
                btnEnviar.disabled = false;
                btnEnviar.innerHTML = 'Enviar Oferta';
                return;
            }
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = 'Enviar Oferta';
            if (data && typeof data.erro !== "undefined" && data.erro) {
                showStatus("Erro: " + data.erro, "danger");
            } else if (data && data.mensagem) {
                showStatus(data.mensagem, "success");
                // Limpa seleção após sucesso
                document.querySelectorAll('input[name="item_ids"]:checked').forEach(cb => cb.checked = false);
            } else {
                showStatus("Resposta inesperada do servidor.", "danger");
            }
        })
        .catch(error => {
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = 'Enviar Oferta';
            showStatus("Erro ao enviar oferta: " + error.message, "danger");
        });
    });

    function showStatus(msg, type) {
        const statusDiv = document.getElementById("status");
        statusDiv.innerHTML = `<div class="alert alert-${type}" role="alert">${msg}</div>`;
    }

    <div id="status" class="mt-3 text-center" aria-live="polite"></div>