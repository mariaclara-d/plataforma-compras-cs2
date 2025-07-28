// Simple informational popup for trade protection policy
document.addEventListener('DOMContentLoaded', function() {
    // Only show this popup once per session for non-logged users
    if (!sessionStorage.getItem('trade_policy_shown') && !document.body.classList.contains('logged-in')) {
        
        // Show after 3 seconds on page
        setTimeout(function() {
            Swal.fire({
                title: '🛡️ Política de Proteção Steam',
                html: `
                    <div class="text-start">
                        <p><strong>Importante:</strong> De acordo com as políticas da Steam:</p>
                        <ul class="text-start">
                            <li>Todas as vendas ficam protegidas por <strong>7 dias</strong></li>
                            <li>Saques só ficam disponíveis após este período</li>
                            <li>Isso garante segurança para todos os usuários</li>
                        </ul>
                        <p class="text-muted small mt-3">Esta é uma política obrigatória da Steam, não da nossa plataforma.</p>
                    </div>
                `,
                icon: 'info',
                confirmButtonText: 'Entendi',
                confirmButtonColor: '#007bff',
                allowOutsideClick: false,
                customClass: {
                    popup: 'trade-policy-popup'
                }
            }).then(() => {
                sessionStorage.setItem('trade_policy_shown', 'true');
            });
        }, 3000);
    }
});

// Add some custom styling
const style = document.createElement('style');
style.textContent = `
    .trade-policy-popup {
        font-family: 'PT Sans', sans-serif;
    }
    .trade-policy-popup ul {
        margin: 0;
        padding-left: 20px;
    }
    .trade-policy-popup li {
        margin-bottom: 8px;
    }
`;
document.head.appendChild(style);
