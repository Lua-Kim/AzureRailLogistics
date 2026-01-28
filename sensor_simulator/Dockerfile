# Sensor Simulator Dockerfile for Azure IoT Edge
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY sensor_simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sensor_simulator/ .
COPY sensor_adapter /app/sensor_adapter

# Run the simulator
CMD ["python", "sensor_data_generator.py"]
