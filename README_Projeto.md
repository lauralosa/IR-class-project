# 🔍 RepositóriUM Search Engine (Equipa)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![React Version](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

O **RepositóriUM Search Engine** é um sistema completo de Processamento e Recuperação de Informação (PRI) desenvolvido para pesquisar, analisar e classificar publicações académicas extraídas da Universidade do Minho. 

O sistema implementa de raiz estruturas de dados avançadas (Índices Invertidos, Skip Pointers), algoritmos clássicos de *Information Retrieval* (TF-IDF, Boolean Model) e Processamento de Linguagem Natural (NLP), acompanhados por um Dashboard interativo.

---

## 🚀 Funcionalidades Principais (Features)

### 1. Motor de Pesquisa Duplo (NLP)
O sistema mantém dois índices invertidos em memória para comparação direta de performance:
* **Stemming (Porter Stemmer):** Redução agressiva e rápida.
* **Lematização (WordNet):** Redução baseada em dicionário.

### 2. Algoritmos de Ranking
* **TF-IDF Customizado:** Implementação matemática de raiz com Similaridade do Cosseno.
* **TF-IDF Scikit-Learn:** Para comparação de *baselines*.
* **Modelo Booleano Rigoroso:** Suporte para queries avançadas (`AND`, `OR`, `NOT`) com avaliação de precedência.

### 3. Machine Learning (Classificação Automática)
* O sistema possui um modelo **Multinomial Naïve Bayes** integrado que, durante a indexação, treina e prevê a categoria das publicações com base nos títulos e resumos (IA & Robótica, Data Science, Engenharia Geral, etc.).

### 4. Frontend Avançado
* **Construtor Visual de Queries:** *Drag & drop* para queries booleanas complexas sem saber sintaxe.
* **Comparador de Performance (A/B):** Executa procuras em paralelo em ambos os motores e compara o Tempo de Indexação e Recall.
* **Timeline de Autores e Rede de Colaboração.**

---

## 💻 Como Executar o Projeto

### Pré-requisitos
* Python 3.10+
* Node.js 18+ (e npm)

### 1. Configurar o Backend (API & Motor de Pesquisa)

O Backend gere o *scraping*, a indexação e responde aos pedidos RESTful do frontend.

```bash
# 1. Criar um ambiente virtual (na pasta raiz)
python -m venv venv

# 2. Ativar o ambiente virtual
# No Windows:
venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate

# 3. Instalar dependências de Python
pip install -r requirements.txt

# 4. Iniciar a API (FastAPI)
uvicorn src.api.main:app --reload
```
A API ficará disponível em `http://localhost:8000`. Pode consultar a **documentação Swagger** (OpenAPI) em `http://localhost:8000/docs`.

### 2. Configurar o Frontend (Interface React)

O Frontend é o portal gráfico do utilizador.

```bash
# 1. Navegar para a pasta do frontend
cd src/frontend

# 2. Instalar dependências Node
npm install

# 3. Iniciar o servidor de desenvolvimento
npm run dev
```
A plataforma ficará acessível em `http://localhost:5173`.

---


## 🐳 Como Executar o Projeto (Via Docker - Recomendado)

A forma mais rápida e segura de rodar o ecossistema completo (Backend + Frontend) sem necessidade de instalar dependências locais é através do **Docker**.

### Pré-requisitos
* **Docker Desktop** instalado e a correr ([Download Docker](https://www.docker.com/products/docker-desktop/))

### 🚀 Arranque Único

Na pasta raiz do projeto (onde se encontra o ficheiro `docker-compose.yml`), executa o seguinte comando no teu terminal:

```bash
docker-compose up --build
```
---

## 🧪 Executar Testes Automatizados

Para garantir a fiabilidade das estruturas de dados (índice, skips, NLP), pode correr a bateria de testes automatizados com o `pytest`:

```bash
# Executar todos os testes na pasta raiz
pytest tests/ -v
```

---

## 🏗️ Arquitetura do Sistema

* `src/api/` - Controladores REST, *endpoints* FastAPI e tradução das queries do frontend.
* `src/search/` - O núcleo do motor de busca (Indexador, Query Engine, Processamento de Texto).
* `src/ml/` - Módulo de Machine Learning (Naïve Bayes).
* `src/frontend/` - Aplicação SPA em React.
* `data/` - Base de dados JSON local (índices serializados e documentos extraídos).

---

> Projeto desenvolvido no âmbito da Unidade Curricular de Processamento e Recuperação de Informação (Mestrado) da Universidade do Minho.
