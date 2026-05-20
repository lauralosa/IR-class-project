# Imagem leve baseada em Python
FROM python:3.10-slim

# Definir a pasta de trabalho dentro do contentor
WORKDIR /app

# Instalar dependências essenciais do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar os ficheiros de requisitos primeiro (otimização de cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Descarregar pacotes essenciais do NLTK (Stemmer, Stopwords, etc.)
RUN python -m nltk.downloader punkt stopwords wordnet omw-1.4

# Copiar todo o código-fonte
COPY . .

# Expor a porta que a API vai usar
EXPOSE 8000

# Comando para arrancar a API em produção (acessível do exterior do contentor)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
