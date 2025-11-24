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

# Expose port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATABASE_URL=sqlite:///./data/raisemyhand.db
ENV BASE_URL=http://localhost:8000
ENV TIMEZONE=UTC
ENV CREATE_DEFAULT_API_KEY=false

# Use entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
