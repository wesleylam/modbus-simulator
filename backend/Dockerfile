FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Port 502  = Modbus TCP
# Port 8000 = REST API + WebSocket
EXPOSE 502 8000

# Default CSV path (override via CSV_PATH env var or volume mount)
ENV CSV_PATH=/app/registers.csv

CMD ["python", "main.py"]
