

# Projeto: Plataforma de Compras de Itens de CS2 (Counter-Strike 2)

Este projeto é uma plataforma de compras de itens de CS2 (skins, armas, etc.), onde os usuários podem fazer login via Steam, listar itens de seu inventário para venda e enviar ofertas diretamente para o site. O site utiliza APIs da Steam e a biblioteca `steampy` para gerenciar autenticação, inventário e ofertas.

---

## 🚀 Tecnologias Utilizadas

- **Backend:** Flask (Python)
- **Frontend:** Bootstrap, HTML, CSS, JavaScript
- **Autenticação:** Steam OpenID
- **APIs Externas:**
  - Steam API (para autenticação e inventário)
  - Steam Web API (para informações de itens e usuários)
- **Bibliotecas:**
  - `steampy` (para gerenciamento de ofertas e trade links)
  - `requests` (para integração com APIs)
- **Banco de Dados:** PostgreSQL 
- **Outras Ferramentas:** Git, Pip (gerenciamento de dependências)

---

## ⚙️ Funcionalidades

1. **Autenticação via Steam:**
   - Os usuários fazem login usando suas contas da Steam através do Steam OpenID.
   - Após o login, são redirecionados para o dashboard.

2. **Dashboard do Usuário:**
   - O usuário insere seu **Trade Link** para permitir transações.
   - O inventário do usuário é carregado usando a Steam API.

3. **Seleção de Itens para Venda:**
   - O usuário seleciona itens do inventário para vender ao site.
   - Os itens selecionados são enviados como uma oferta ao site usando a biblioteca `steampy`.

4. **Gerenciamento de Ofertas:**
   - O site aceita ofertas de itens e processa as transações.
   - Ofertas são gerenciadas automaticamente pela biblioteca `steampy`.

---

## 📋 Pré-requisitos

Antes de executar o projeto, certifique-se de ter instalado:

- Python 3.8 ou superior
- Pip (gerenciador de pacotes do Python)
- Conta de desenvolvedor na Steam (para obter chaves de API)

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🙋‍♂️ Autor

- **Maria Clara Guimarães**  
- GitHub: [mariaclara-d](https://github.com/mariaclara-d)  
- LinkedIn: [maria-clara-dev](https://www.linkedin.com/in/maria-clara-dev/)  

---

�
