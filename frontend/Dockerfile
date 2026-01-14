# Build stage
FROM node:24-alpine@sha256:266f8dae214bb44a1caefb9ca4c79e0a6dd363ed9d807b82222efa0e53e5288a AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --ignore-scripts

COPY . .
# Set base path to '/' for Docker
ENV VITE_BASE_URL=/
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
