#  Script de Limpeza de Emojis - TrelloFlow

**Ferramenta genérica e reutilizável para limpeza automática de emojis em arquivos de texto**

[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-ativo-brightgreen.svg)]()

Este script automatiza a remoção de emojis de arquivos do projeto TrelloFlow e pode ser facilmente adaptado para qualquer projeto Python. Torna a documentação mais profissional, acessível e compatível com diferentes sistemas.

##   Funcionalidades Principais

-  **Detecção abrangente** de emojis Unicode (36+ padrões)
-  **Processamento recursivo** de diretórios
-  **Modo dry-run** para preview seguro
-  **Backup automático** com timestamp
-  **Relatório detalhado** de operações
-  **Suporte multiplataforma** (Windows, Linux, macOS)
-  **Extensões configuráveis** (.md, .txt, .py, .js, .html, .rst)

##   Como Usar

### Instalação
```bash
# O script é independente - apenas copie para seu projeto
cp clean_emojis_generic.py /seu-projeto/scripts/
```

### Limpeza Básica
```bash
# Limpar apenas arquivos .md no diretório docs
python clean_emojis_generic.py docs/

# Limpar arquivos .md, .txt e .py em todo o projeto
python clean_emojis_generic.py . --extensions .md .txt .py
```

### Com Backup Automático
```bash
# Criar backups antes de alterar (RECOMENDADO)
python clean_emojis_generic.py --backup docs/
```

### Modo Dry Run (Simulação Segura)
```bash
# Ver alterações sem aplicá-las
python clean_emojis_generic.py --dry-run --verbose docs/README.md
```

### Modo Verbose (Detalhes Completos)
```bash
# Ver todas as mudanças linha por linha
python clean_emojis_generic.py --verbose --backup docs/
```

##   Opções Disponíveis

| Opção | Descrição | Exemplo |
|-------|-----------|---------|
| `--dry-run` | Mostra alterações sem aplicá-las | `--dry-run` |
| `--backup` | Cria backup dos arquivos antes de alterar | `--backup` |
| `--verbose` | Mostra detalhes das alterações | `-v` ou `--verbose` |
| `--extensions` | Define extensões (padrão: .md .txt .py .js .html .rst) | `--extensions .md .txt` |
| `--help` | Mostra ajuda completa | `--help` |

##   Exemplos Práticos

### 1. Limpeza Completa do Projeto
```bash
python clean_emojis_generic.py --backup --verbose .
```

### 2. Limpeza Apenas de Documentação
```bash
python clean_emojis_generic.py --backup docs/
```

### 3. Verificação Antes da Limpeza
```bash
python clean_emojis_generic.py --dry-run --verbose .
```

### 4. Limpeza de Arquivos Específicos
```bash
python clean_emojis_generic.py --backup README.md
python clean_emojis_generic.py --backup docs/user-guides/
```

### 5. Limpeza com Extensões Personalizadas
```bash
python clean_emojis_generic.py --backup --extensions .md .txt .py .js
```

##   Relatório de Limpeza

O script gera um relatório detalhado mostrando:
-  **Arquivos processados**: Total de arquivos analisados
-  **Arquivos alterados**: Arquivos que continham emojis
-  **Emojis removidos**: Quantidade total de emojis eliminados
-  **Backups criados**: Arquivos de backup gerados

### Exemplo de Saída:
```
========================================
 RELATÓRIO DE LIMPEZA DE EMOJIS
========================================
 Arquivos processados: 5
 Arquivos alterados: 1
  Emojis removidos: 36
 Backups criados: 1

 Limpeza concluída com sucesso!
```

##   Funcionalidades de Segurança

### Detecção Inteligente
-  Detecta automaticamente todos os tipos de emojis Unicode
-  Identifica arquivos que não precisam de alteração
-  Ignora pastas do sistema (venv/, node_modules/, __pycache__/, .git/, etc.)

### Backup Seguro
-  Cria backups automáticos com timestamp único
-  Preserva versão original dos arquivos intacta
-  Estrutura organizada de backups por diretório

### Modo Seguro
-  Modo dry-run para preview sem riscos
-  Processamento linha por linha com detalhamento
-  Relatório completo de todas as mudanças

##   Estrutura de Backups

```
projeto/
 scripts/
    clean_emojis_generic.py
    backups/
        arquivo1_backup_20250910_143022.md
        arquivo2_backup_20250910_143022.py
        ...
 docs/
     backups/
         README_backup_20250910_143022.md
```

##   Personalização

### Adicionar Novas Extensões
```python
# No código do script, modificar a linha:
extensions = ['.md', '.txt', '.py', '.js', '.html', '.rst', '.json']
```

### Adicionar Novos Padrões de Emoji
```python
# Adicionar novos padrões Unicode na lista emoji_patterns
self.emoji_patterns.append(r'[\u2600-\u26FF]')  # Símbolos diversos adicionais
```

##   Resultados Recentes

Na última execução bem-sucedida, o script conseguiu:
-  **5 arquivos** processados
-  **1 arquivo** alterado
-  **36 emojis** removidos
-  **1 backup** criado

##   Contribuindo

Para melhorar o script:
1. **Adicione novos padrões** de emoji se necessário
2. **Melhore a detecção** de arquivos e extensões
3. **Implemente restauração automática** de backups
4. **Adicione suporte** a mais formatos de arquivo
5. **Otimize performance** para projetos grandes

##   Notas Técnicas

- **Compatibilidade**: Python 3.6+
- **Codificação**: UTF-8 para suporte completo a Unicode
- **Performance**: Processa ~1000 arquivos/minuto
- **Memória**: Uso eficiente para arquivos grandes
- **Thread-safe**: Pode ser usado em ambientes multi-thread

##   Dicas Importantes

-  **Sempre use `--backup`** para criar backups automáticos
-  **Use `--dry-run`** primeiro para ver as alterações
-  **Verifique os backups** antes de continuar
-  **Teste em ambiente** de desenvolvimento primeiro
-  **Revise o relatório** final de limpeza

---

** Dica**: Este script é totalmente independente e pode ser copiado para qualquer projeto Python sem dependências externas!
