# utils/log_cleanup.py
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_old_logs(days_to_keep=30, log_directory="logs"):
    """
    Remove logs antigos para evitar acúmulo excessivo de arquivos.
    
    Args:
        days_to_keep (int): Número de dias de logs para manter
        log_directory (str): Diretório dos logs
    """
    logger = logging.getLogger(__name__)
    
    try:
        log_dir = Path(log_directory)
        if not log_dir.exists():
            logger.warning(f"Diretório de logs não encontrado: {log_directory}")
            return
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for log_file in log_dir.glob("*.log*"):
            try:
                # Verificar data de modificação do arquivo
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    log_file.unlink()
                    removed_count += 1
                    logger.info(f"Log antigo removido: {log_file.name}")
                    
            except Exception as e:
                logger.error(f"Erro ao remover log {log_file.name}: {str(e)}")
        
        logger.info(f"Limpeza de logs concluída. {removed_count} arquivos removidos.")
        
    except Exception as e:
        logger.error(f"Erro durante limpeza de logs: {str(e)}")

def get_log_statistics(log_directory="logs"):
    """
    Retorna estatísticas dos arquivos de log.
    
    Returns:
        dict: Estatísticas dos logs
    """
    try:
        log_dir = Path(log_directory)
        if not log_dir.exists():
            return {"error": "Diretório de logs não encontrado"}
        
        stats = {
            "total_files": 0,
            "total_size_mb": 0,
            "oldest_file": None,
            "newest_file": None,
            "files": []
        }
        
        for log_file in log_dir.glob("*.log*"):
            file_stat = log_file.stat()
            file_size_mb = file_stat.st_size / (1024 * 1024)
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            
            stats["total_files"] += 1
            stats["total_size_mb"] += file_size_mb
            
            if stats["oldest_file"] is None or file_mtime < stats["oldest_file"]:
                stats["oldest_file"] = file_mtime
                
            if stats["newest_file"] is None or file_mtime > stats["newest_file"]:
                stats["newest_file"] = file_mtime
            
            stats["files"].append({
                "name": log_file.name,
                "size_mb": round(file_size_mb, 2),
                "modified": file_mtime.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        return stats
        
    except Exception as e:
        return {"error": f"Erro ao obter estatísticas: {str(e)}"}

if __name__ == "__main__":
    # Executar limpeza se chamado diretamente
    print("Iniciando limpeza de logs...")
    cleanup_old_logs(days_to_keep=30)
    
    print("\nEstatísticas dos logs:")
    stats = get_log_statistics()
    if "error" not in stats:
        print(f"Total de arquivos: {stats['total_files']}")
        print(f"Tamanho total: {stats['total_size_mb']} MB")
        if stats['oldest_file']:
            print(f"Arquivo mais antigo: {stats['oldest_file'].strftime('%Y-%m-%d %H:%M:%S')}")
        if stats['newest_file']:
            print(f"Arquivo mais recente: {stats['newest_file'].strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"Erro: {stats['error']}")
