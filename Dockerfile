# Usa uma imagem base com Python
FROM python:3.10-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia o arquivo de dependências para o contêiner
COPY requirements.txt .

# Instala as dependências do projeto
RUN pip install --default-timeout=100 --no-cache-dir -i https://pypi.org/simple -r requirements.txt

# Copia todos os arquivos do projeto para o contêiner
COPY . .

# Define as variáveis de ambiente para o Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Expõe a porta 5000 para acesso ao Flask
EXPOSE 5000

# Comando para rodar o servidor Flask
CMD ["flask", "run", "--host=0.0.0.0"]
