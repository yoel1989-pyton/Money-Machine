# ============================================================
# MONEY MACHINE - ELITE N8N DOCKERFILE
# The Autonomous Omni-Channel Revenue Engine
# ============================================================
# This custom n8n image includes:
# - FFmpeg (video/audio manipulation)
# - Python 3 (automation scripts, data processing)
# - yt-dlp (legal content research)
# - MoviePy (programmatic video editing)
# - Chromium (for official API OAuth flows)
# ============================================================

FROM n8nio/n8n:latest

USER root

# ============================================================
# SYSTEM DEPENDENCIES - "THE MUSCLES"
# ============================================================
RUN apk add --no-cache \
    # Video/Audio Processing
    ffmpeg \
    # Python Runtime
    python3 \
    py3-pip \
    # Build tools for Python packages
    build-base \
    python3-dev \
    # Chromium for OAuth flows (official APIs only)
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    # Utilities
    bash \
    curl \
    jq \
    git

# ============================================================
# PYTHON PACKAGES - "THE HANDS"
# ============================================================
RUN pip3 install --no-cache-dir --break-system-packages \
    # Video/Content Tools
    yt-dlp \
    moviepy \
    Pillow \
    # Data Processing
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
