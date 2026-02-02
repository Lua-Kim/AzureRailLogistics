# Backend Service Dockerfile for Azure IoT Edge
FROM python:3.11-slim
LABEL build_marker="backend_dockerfile_no_sensor_adapter"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Clean Python cache
RUN find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "backend_main:app", "--host", "0.0.0.0", "--port", "8000"]
