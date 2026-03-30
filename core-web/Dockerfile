FROM node:20-slim

WORKDIR /app

# Copy package files first for caching
COPY package.json package-lock.json* ./
COPY .npmrc ./

# Install dependencies
ARG HUGEICONS_TOKEN
RUN npm ci || npm install

# Copy source code
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host"]
