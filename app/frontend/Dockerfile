# ---------- Base deps ----------
FROM node:20-alpine AS base
WORKDIR /app
RUN apk add --no-cache libc6-compat

# ---------- Build stage ----------
FROM base AS builder
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies
RUN npm install --no-audit --no-fund
COPY . .

# Build argument for API URL
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application
RUN npm run build

# ---------- Production stage ----------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0

# Copy public folder only if it exists
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
