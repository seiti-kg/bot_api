# Base image
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta (caso esteja rodando uma aplicação web)
EXPOSE 5000

# Comando de inicialização
CMD ["python", "app.py"]
