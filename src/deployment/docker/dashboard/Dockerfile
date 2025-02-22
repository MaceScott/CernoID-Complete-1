FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs

ENV PYTHONPATH=/app
ENV DATA_PATH=/app/data
ENV LOG_PATH=/app/logs

EXPOSE 8003

CMD ["python3", "-m", "src.core.admin.dashboard"] 