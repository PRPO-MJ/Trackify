# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Define build arguments for environment variables
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_USER_SERVICE_URL
ARG VITE_GOALS_SERVICE_URL
ARG VITE_ENTRIES_SERVICE_URL
ARG VITE_MAILER_SERVICE_URL
ARG VITE_PDF_SERVICE_URL
ARG VITE_APP_NAME
ARG VITE_APP_VERSION

# Set environment variables from build args
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_USER_SERVICE_URL=$VITE_USER_SERVICE_URL
ENV VITE_GOALS_SERVICE_URL=$VITE_GOALS_SERVICE_URL
ENV VITE_ENTRIES_SERVICE_URL=$VITE_ENTRIES_SERVICE_URL
ENV VITE_MAILER_SERVICE_URL=$VITE_MAILER_SERVICE_URL
ENV VITE_PDF_SERVICE_URL=$VITE_PDF_SERVICE_URL
ENV VITE_APP_NAME=$VITE_APP_NAME
ENV VITE_APP_VERSION=$VITE_APP_VERSION

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy environment file
COPY .env* ./

# Copy source
COPY . .

# Build the application (Vite will read .env files at build time)
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the production build
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start the application
CMD ["serve", "-s", "dist", "-l", "3000"]
