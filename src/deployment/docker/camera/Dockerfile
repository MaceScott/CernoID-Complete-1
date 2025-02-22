FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Create directories
RUN mkdir -p /app/data /app/logs

ENV PYTHONPATH=/app
ENV DATA_PATH=/app/data
ENV LOG_PATH=/app/logs

EXPOSE 8001

CMD ["python3", "-m", "src.core.camera.coordinator"] 