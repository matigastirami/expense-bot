# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Accept build arguments for Vite
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_TELEGRAM_BOT_NAME

# Set as environment variables for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_TELEGRAM_BOT_NAME=$VITE_TELEGRAM_BOT_NAME

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application (Vite will use the ENV vars)
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
