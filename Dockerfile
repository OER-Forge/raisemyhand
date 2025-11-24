FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Note: Port is configured via docker-compose.yml and .env
# No EXPOSE needed as port mapping is explicit in compose file

# Use entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
