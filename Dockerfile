# Usa uma imagem base do Python
FROM python:3.12.3-slim

# Instalar pacotes necessários para locales e Chromium
RUN apt-get update && apt-get install -y \
    locales \
    && rm -rf /var/lib/apt/lists/*  # Remove cache do apt para deixar a imagem menor

# Adicionar suporte para pt_BR.UTF-8
RUN sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# Definir locale padrão
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8

# Define o diretório de trabalho dentro do container
WORKDIR /src

# Copia os arquivos de dependências primeiro (para cache eficiente)
COPY requirements.txt ./

# Cria o ambiente virtual dentro do container
RUN python -m venv /opt/venv

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/*

# Ativa o ambiente virtual e instala as dependências
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt "fastapi[standard]" "pymongo"

# Copia o restante do código
COPY . .

# Define o PATH para usar o venv por padrão
ENV PATH="/opt/venv/bin:$PATH"

# Expor a porta do FastAPI
EXPOSE 8000

# Comando para rodar o servidor FastAPI sem Poetry
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
