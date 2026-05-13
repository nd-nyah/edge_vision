FROM node:20

WORKDIR /app

# Install dependencies first (better caching)
COPY package.json package-lock.json ./
RUN npm install

# Copy source code
COPY . .

# Prevent container using local node_modules from bind mount
ENV CHOKIDAR_USEPOLLING=true

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# FROM node:20

# WORKDIR /app

# COPY package.json package-lock.json ./
# RUN npm install

# COPY . .

# EXPOSE 5173

# CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# FROM node:20-alpine

# WORKDIR /app

# COPY package*.json ./

# RUN npm install

# COPY . .

# EXPOSE 5173

# CMD ["npm", "run", "dev", "--", "--host"]