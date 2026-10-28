FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install MongoDB Database Tools
RUN curl -fsSL https://pgp.mongodb.com/server-8.0.asc \
    | gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg \
    && echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" \
    > /etc/apt/sources.list.d/mongodb-org-8.0.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends mongodb-database-tools \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and backup directory
RUN groupadd -g 10001 kaliuser \
    && useradd -u 10001 -g kaliuser -s /usr/sbin/nologin -m kaliuser \
    && mkdir -p /opt/mongodb-backups \
    && chown -R kaliuser:kaliuser /opt/mongodb-backups /app

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY kali/ ./kali/
COPY config/ ./config/

RUN chown -R kaliuser:kaliuser /app

USER kaliuser

CMD ["python", "-m", "kali.main"]