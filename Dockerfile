FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Ensure project root is importable
ENV PYTHONPATH=/app

# Cloud Run sets PORT env var
ENV PORT=8080

EXPOSE 8080

# Production server
CMD exec gunicorn api.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
