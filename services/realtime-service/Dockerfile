FROM node:18-alpine AS base

FROM base AS development
WORKDIR /app
COPY package.json tsconfig.json ./
RUN npm install
COPY src ./src
CMD ["npm", "run", "dev"]

FROM base AS production
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY . .
RUN npm run build
CMD ["npm", "start"]
