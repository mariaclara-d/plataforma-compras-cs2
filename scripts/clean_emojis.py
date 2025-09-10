#!/usr/bin/env python3
"""
Script Genérico para limpeza automática de emojis em arquivos
Versão independente - pode ser copiada para qualquer projeto

Uso:
    python clean_emojis.py [--dry-run] [--backup] [--verbose]

Opções:
    --dry-run    : Mostra alterações sem aplicá-las
    --backup     : Cria backup dos arquivos antes de alterar
    --verbose    : Mostra detalhes das alterações
"""

import os
import re
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

class EmojiCleaner:
    """Classe para limpeza de emojis em arquivos"""

    def __init__(self, dry_run: bool = False, backup: bool = False, verbose: bool = False) -> None:
        self.dry_run = dry_run
        self.backup = backup
        self.verbose = verbose
        self.stats = {
            'files_processed': 0,
            'files_changed': 0,
            'emojis_removed': 0,
            'backups_created': 0
        }

        # Padrões de emojis Unicode abrangentes
        self.emoji_patterns = [
            r'[\U0001F600-\U0001F64F]',  # Emoticons
            r'[\U0001F300-\U0001F5FF]',  # Símbolos e pictogramas
            r'[\U0001F680-\U0001F6FF]',  # Transporte e símbolos
            r'[\U0001F1E0-\U0001F1FF]',  # Bandeiras
            r'[\U00002500-\U00002BEF]',  # Símbolos diversos
            r'[\U00002702-\U000027B0]',  # Dingbats
            r'[\U000024C2-\U0001F251]',  # Símbolos alfanuméricos
            r'[\U0001f926-\U0001f937]',  # Gestos
            r'[\U00010000-\U0010ffff]',  # Outros símbolos
            r'[\u2640-\u2642]',          # Símbolos de gênero
            r'[\u2600-\u2B55]',          # Símbolos diversos
            r'[\u200d]',                 # Zero width joiner
            r'[\u23cf]',                 # Eject symbol
            r'[\u23e9]',                 # Fast forward
            r'[\u231a]',                 # Watch
            r'[\ufe0f]',                 # Variation selector
            r'[\u3030]',                 # Wavy dash
        ]

        # Compilar padrão combinado
        self.emoji_regex = re.compile('|'.join(self.emoji_patterns), flags=re.UNICODE)

    def has_emojis(self, text: str) -> bool:
        """Verifica se o texto contém emojis"""
        return bool(self.emoji_regex.search(text))

    def remove_emojis(self, text: str) -> str:
        """Remove todos os emojis do texto"""
        return self.emoji_regex.sub('', text)

    def create_backup(self, file_path: str) -> None:
        """Cria backup do arquivo"""
        if not self.backup:
            return

        backup_dir = Path(file_path).parent / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{Path(file_path).stem}_backup_{timestamp}{Path(file_path).suffix}"
        backup_path = backup_dir / backup_name

        shutil.copy2(file_path, backup_path)

        if self.verbose:
            print(f"  Backup criado: {backup_path}")

        self.stats['backups_created'] += 1

    def process_file(self, file_path: str) -> None:
        """Processa um arquivo individual"""
        self.stats['files_processed'] += 1

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not self.has_emojis(content):
                if self.verbose:
                    print(f"  Nenhum emoji encontrado: {file_path}")
                return

            # Contar emojis antes da remoção
            original_count = len(self.emoji_regex.findall(content))

            # Remover emojis
            cleaned_content = self.remove_emojis(content)

            if self.dry_run:
                print(f"  [DRY RUN] {file_path}: {original_count} emojis encontrados")
                if self.verbose:
                    # Mostrar diferenças
                    lines_orig = content.split('\n')
                    lines_clean = cleaned_content.split('\n')
                    for i, (orig, clean) in enumerate(zip(lines_orig, lines_clean)):
                        if orig != clean:
                            print(f"    Linha {i+1}: {orig}")
                            print(f"    -> {clean}")
                return

            # Criar backup se necessário
            self.create_backup(file_path)

            # Salvar arquivo limpo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)

            self.stats['files_changed'] += 1
            self.stats['emojis_removed'] += original_count

            print(f"  {file_path}: {original_count} emojis removidos")

            if self.verbose:
                # Mostrar algumas mudanças
                lines_orig = content.split('\n')
                lines_clean = cleaned_content.split('\n')
                changes_shown = 0
                for i, (orig, clean) in enumerate(zip(lines_orig, lines_clean)):
                    if orig != clean and changes_shown < 3:
                        print(f"    Linha {i+1}: '{orig}' -> '{clean}'")
                        changes_shown += 1

        except Exception as e:
            print(f"  Erro ao processar {file_path}: {e}")

    def process_directory(
            self, directory: str, extensions: Optional[List[str]] = None) -> None:
        """Processa todos os arquivos em um diretório ou arquivo específico"""
        if extensions is None:
            extensions = ['.md', '.txt', '.py', '.js', '.html', '.rst']

        # Pastas a ignorar
        ignore_dirs = {
            'venv', 'node_modules', '__pycache__', '.git', '.pytest_cache',
            'backups', 'build', 'dist', '.next', '.nuxt', 'coverage',
            'htmlcov', '.mypy_cache', '.tox', '.eggs', '*.egg-info',
            '.vscode', '.idea', 'target', 'bin', 'obj'
        }

        # Verificar se é um arquivo específico
        if os.path.isfile(directory):
            if any(directory.endswith(ext) for ext in extensions):
                self.process_file(directory)
            return

        # Processar diretório
        for root, dirs, files in os.walk(directory):
            # Filtrar diretórios a ignorar
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    self.process_file(file_path)

    def print_report(self) -> None:
        """Imprime relatório final"""
        print("\n" + "="*50)
        print(" RELATÓRIO DE LIMPEZA DE EMOJIS")
        print("="*50)
        print(f" Arquivos processados: {self.stats['files_processed']}")
        print(f" Arquivos alterados: {self.stats['files_changed']}")
        print(f"  Emojis removidos: {self.stats['emojis_removed']}")
        print(f" Backups criados: {self.stats['backups_created']}")

        if self.dry_run:
            print("\n MODO DRY RUN - Nenhuma alteração foi aplicada")
        else:
            print("\n Limpeza concluída com sucesso!")

def main():
    parser = argparse.ArgumentParser(
        description='Limpa emojis de arquivos de texto',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python clean_emojis.py --dry-run --verbose
  python clean_emojis.py --backup
  python clean_emojis.py --dry-run docs/
  python clean_emojis.py --extensions .md .txt .py
        """
    )

    parser.add_argument('--dry-run', action='store_true',
                       help='Mostra alterações sem aplicá-las')
    parser.add_argument('--backup', action='store_true',
                       help='Cria backup dos arquivos antes de alterar')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostra detalhes das alterações')
    parser.add_argument('--extensions', nargs='+',
                       default=['.md', '.txt', '.py', '.js', '.html', '.rst'],
                       help='Extensões de arquivo para processar')
    parser.add_argument('directory', nargs='?', default='.',
                       help='Diretório para processar (padrão: atual)')

    args = parser.parse_args()

    print(" Limpador de Emojis - Versão Genérica")
    print("="*40)

    if args.dry_run:
        print(" Modo DRY RUN ativado - nenhuma alteração será aplicada")

    if args.backup:
        print(" Modo BACKUP ativado - backups serão criados")

    # Criar instância do limpador
    cleaner = EmojiCleaner(
        dry_run=args.dry_run,
        backup=args.backup,
        verbose=args.verbose
    )

    # Processar arquivos
    print(f"\n Processando arquivos em: {args.directory}")
    cleaner.process_directory(args.directory, args.extensions)

    # Imprimir relatório
    cleaner.print_report()

if __name__ == '__main__':
    main()
