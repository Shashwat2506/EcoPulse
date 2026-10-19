# ==============================================================================
# EcoPulse: Smart Sustainability Tracker
# Production Multi-Stage / Lightweight Containerization
# ==============================================================================

FROM python:3.11-slim as base

# Set environment variables to optimize Python within Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Set working directory
WORKDIR /app

# Install dependencies in a single layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create a dedicated non-root user and set directory permissions for SQLite persistence
RUN groupadd -g 10001 ecopulse && \
    useradd -u 10001 -g ecopulse -s /bin/sh -d /app ecopulse && \
    chown -R ecopulse:ecopulse /app

# Switch to non-root user
USER ecopulse

# Expose application port
EXPOSE 5000

# Container liveness health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/healthz')" || exit 1

# Launch production WSGI application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "app:app"]
