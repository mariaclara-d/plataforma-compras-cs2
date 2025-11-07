@echo off
echo === SISTEMA ADMIN FLASK ===
echo.

echo 1. Parando containers existentes...
docker-compose down

echo.
echo 2. Reconstruindo imagem...
docker-compose build --no-cache web

echo.
echo 3. Iniciando containers...
docker-compose up -d

echo.
echo 4. Aguardando servicos iniciarem...
timeout /t 10

echo.
echo 5. Verificando status...
docker ps

echo.
echo === SISTEMA PRONTO ===
echo.
echo Acesse: http://localhost:5000/admin/login
echo Usuario: admin
echo Senha: admin123
echo.
echo Para verificar logs: docker-compose logs web
echo Para parar: docker-compose down
echo.
pause
