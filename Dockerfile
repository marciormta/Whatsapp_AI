# Use uma imagem base do Python 3.12-slim
FROM python:3.12-slim

# Evita criação de arquivos .pyc e força logs para stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Adiciona o diretório /app ao PYTHONPATH para que os imports absolutos funcionem
ENV PYTHONPATH=/app

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (incluindo pg_config)
RUN apt-get update && apt-get install -y gcc libpq-dev

# Copia os arquivos essenciais para instalação de dependências
COPY pyproject.toml ./
COPY .env ./

# Atualiza o pip e instala o uv
RUN pip install --upgrade pip && pip install uv

# Instala o pacote em modo editável no ambiente do container (sem ambiente virtual local)
RUN uv pip install --system --editable .

# Copia o restante do projeto para o container
COPY . .

# Exponha a porta que seu app utilizará (neste exemplo, 8005)
EXPOSE 8005

# Inicia a aplicação executando o módulo app.main
CMD ["uv", "run", "-m", "app.main"]
