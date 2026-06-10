FROM node:18

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-sandbox \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3001

# Limpiar bloqueos de Chrome
RUN rm -rf /root/.cache /root/.config /root/.pki 2>/dev/null || true

CMD ["npm", "start"]
