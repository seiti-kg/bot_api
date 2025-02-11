# Imagem base
FROM python:3.12.3

# Instalar pacotes necessários para locales
RUN apt-get update && apt-get install -y locales

# Adicionar suporte para pt_BR.UTF-8
RUN sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# Definir locale padrão
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8

# Instala Poetry
RUN pip install --upgrade pip
RUN pip install --no-cache-dir poetry

# Define o diretório de trabalho
WORKDIR /src

# Copia os arquivos do projeto
COPY pyproject.toml poetry.lock ./
COPY . .


# Instala as dependências diretamente do requirements.txt com pip
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt "fastapi[standard]" "pymongo"

# Instalar Chromium
RUN apt-get update && apt-get install -y chromium


# Comando para rodar o servidor via FastAPI
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

