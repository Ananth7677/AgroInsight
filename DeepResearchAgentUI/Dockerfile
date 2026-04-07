# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# Serve stage
FROM node:20-alpine

WORKDIR /app

RUN npm install -g http-server

COPY --from=builder /app/dist/DeepResearchAgentUI ./dist

EXPOSE 4200

CMD ["http-server", "dist/browser", "-p", "4200", "--cors"]
