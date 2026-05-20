FROM node:22-alpine

WORKDIR /app

# Copiar os ficheiros de dependências primeiro
COPY package.json package-lock.json* ./

# Forçar a instalação limpa das dependências diretamente no Linux do Docker
RUN npm install

# Só depois copiamos o resto do código
COPY . .

EXPOSE 5173

# O Vite precisa da flag --host para comunicar com o teu Windows
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]