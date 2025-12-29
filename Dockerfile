# ============================================================
# ANOINTMENT BACKEND - Production Dockerfile
# ============================================================
# Forces FFmpeg installation for remix engine
# ============================================================

FROM python:3.11-slim

# Install FFmpeg (REQUIRED for remix engine)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (Docker cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    pandas \
    numpy \
    # API Clients
    google-api-python-client \
    google-auth-oauthlib \
    tweepy \
    praw \
    # TTS (Text-to-Speech)
    edge-tts \
    # HTTP/Automation
    httpx \
    aiohttp \
    beautifulsoup4 \
    # Scheduling
    schedule \
    # Environment
    python-dotenv \
    # Affiliate APIs
    stripe \
    paypalrestsdk \
    # Image/Video Processing
    opencv-python-headless \
    # Data Persistence
    aiosqlite \
    # Machine Learning (lightweight)
    scikit-learn \
    # Retry Logic
    tenacity \
    # YAML Config
    pyyaml \
    # Async job queue
    aiofiles

# ============================================================
# N8N COMMUNITY NODES - "THE AMPLIFIERS"
# ============================================================
# Install community nodes that extend n8n capabilities
RUN cd /usr/local/lib/node_modules/n8n && \
    npm install \
    n8n-nodes-text-manipulation \
    @n8n/n8n-nodes-langchain \
    n8n-nodes-base-python

# ============================================================
# CREATE WORKING DIRECTORIES
# ============================================================
RUN mkdir -p /data/assets /data/output /data/temp /data/logs && \
    chown -R node:node /data

# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================
# Queue Mode for Amplifier Node Scaling
ENV EXECUTIONS_MODE=queue
# Store binary data on filesystem (not DB)
ENV N8N_DEFAULT_BINARY_DATA_MODE=filesystem
# Chromium path for OAuth
ENV CHROME_PATH=/usr/bin/chromium-browser
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
# Python unbuffered output
ENV PYTHONUNBUFFERED=1

# Switch back to node user for security
USER node

# ============================================================
# HEALTHCHECK
# ============================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5678/healthz || exit 1

EXPOSE 5678
