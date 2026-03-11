# Build Stage
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Runtime Stage
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/cache/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend from builder stage
COPY --from=builder /app/dist ./dist

# Copy backend code
COPY api ./api
# COPY backend ./backend  # Only if needed, currently api/ contains the logic

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Start command
# We use uvicorn to run the FastAPI app
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
