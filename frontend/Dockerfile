# Build stage
FROM node:24-alpine@sha256:6ad8c47f099bc2440e0fc42f17a03297fa79955f559f10087cabf377c43ddbce AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --ignore-scripts

COPY . .
# Set base path to '/' for Docker
ENV VITE_BASE_URL=/
RUN npm run build

# Production stage
FROM nginx:alpine@sha256:b0f7830b6bfaa1258f45d94c240ab668ced1b3651c8a222aefe6683447c7bf55

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
