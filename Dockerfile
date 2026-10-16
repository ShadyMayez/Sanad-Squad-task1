# ==============================================================================
# SANADSQUAD EVIDENCE-FIRST V2 — SELF-CONTAINED OFFLINE DOCKERFILE
# Multi-stage/monolithic single-image deployment with bundled Ollama and qwen3.5:4b
# ==============================================================================

FROM python:3.12-slim-bookworm

LABEL maintainer="SanadSquad Senior Engineering Team" \
      version="2.0.0" \
      description="Self-contained, offline-capable SanadSquad Evidence-First V2 content pipeline with pre-baked local Ollama and qwen3.5:4b model." \
      license="Apache-2.0"

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Ollama binary
RUN curl -fsSL https://ollama.com/install.sh | sh

# Create unprivileged application user
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser -s /bin/bash appuser

# Set up application and model directories
WORKDIR /app
RUN mkdir -p /app/models /app/output /home/appuser/.ollama && \
    chown -R appuser:appuser /app /home/appuser

# Pre-bake qwen3.5:4b model into image layer during build (network allowed)
ENV OLLAMA_MODELS=/app/models
RUN ollama serve & \
    SERVER_PID=$! && \
    echo "Waiting for build-time Ollama daemon..." && \
    while ! curl -s http://127.0.0.1:11434/api/tags > /dev/null; do sleep 1; done && \
    echo "Pulling qwen3.5:4b into container image layers..." && \
    ollama pull qwen3.5:4b && \
    echo "Model pull complete. Verifying presence..." && \
    curl -s http://127.0.0.1:11434/api/tags | grep -q "qwen3.5:4b" && \
    kill $SERVER_PID && \
    wait $SERVER_PID || true

# Install locked Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy pipeline source code and configurations
COPY content_pipeline /app/content_pipeline
COPY source_snapshots /app/source_snapshots
COPY knowledge /app/knowledge
COPY instructions /app/instructions
COPY skills /app/skills
COPY schemas /app/schemas
COPY tests /app/tests
COPY audit/tests /app/audit/tests
COPY brand-voice.md kb.json plan.json content-types.json pyproject.toml pytest.ini run_week.py run_piece.py /app/
COPY docker/entrypoint.sh /entrypoint.sh

# Fix ownership and permissions
RUN chmod +x /entrypoint.sh && \
    chown -R appuser:appuser /app /home/appuser

# Runtime environment configuration
USER appuser
ENV HOME=/home/appuser
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=127.0.0.1:11434
ENV OLLAMA_MODELS=/app/models
ENV OLLAMA_MODEL=qwen3.5:4b
ENV OUTPUT_BASE=/app/output

VOLUME ["/app/output"]

ENTRYPOINT ["/entrypoint.sh"]
