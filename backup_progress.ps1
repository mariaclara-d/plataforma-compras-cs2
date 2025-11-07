# Backup automático
 = Get-Date -Format "yyyy-MM-dd_HH-mm"
 = "backup_"

# Copiar arquivos principais
New-Item -ItemType Directory -Force -Path 
Copy-Item services\aiosteampy_service.py \
Copy-Item routes\trade.py \
Copy-Item .env \

Write-Host "✅ Backup criado em: "
