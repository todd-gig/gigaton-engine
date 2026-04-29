FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Ensure project root is importable
ENV PYTHONPATH=/app

# Create data directory for SQLite persistence
RUN mkdir -p /data

# Cloud Run sets PORT env var
ENV PORT=8080
ENV DATABASE_URL=sqlite:///data/gigaton.db

EXPOSE 8080

# Production server
CMD exec gunicorn api.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
